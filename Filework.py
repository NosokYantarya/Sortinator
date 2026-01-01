#Convenient stuff
from enum import Enum
import abc
import operator
#File work
import os
import shutil
import zipfile
#Date work
from datetime import fromtimestamp

###CLASSES
#File class
class FileObj:
    def __init__(self, path):
        if os.path.isfile(path):
            self.UpdateData(path)
        else:
            raise ValueError("Invalid file path")
    
    def UpdateData(self, path):
        NameAndExt = os.splitext(os.basename(path))
        self.Name = NameAndExt[0]
        self.Extension = NameAndExt[1]

        self.MDate = os.path.getmtime(path)
        
        self.ByteSize = os.path.getsize(path)

        self.Number = None

        self.PropertiesCache = None
        
    def Day(self):
        return fromtimestamp(self.MDate).strftime("%d")
    def Month(self):
        return fromtimestamp(self.MDate).strftime("%m")
    def Year(self):
        return fromtimestamp(self.MDate).strftime("%Y")
    
    def SetNumber(self, num):
         self.Number = num
         self.PropertiesCache = None
    
    def GetProperties(self):
        #["num", "name", "ext", "day", "month", "year", "bytes", "kb", "mb", "gb", "tb", "gsize", "gsizename"]
        if self.PropertiesCache == None:
             TGM = ToGreatestMeasure(self.ByteSize)
             self.PropertiesCache = FileProperties([
             self.Number,
             self.Name,
             self.Extension,
             self.Day(),
             self.Month(),
             self.Year(),
             self.ByteSize,
             FromBytesTo(self.ByteSize, "KB"),
             FromBytesTo(self.ByteSize, "MB"),
             FromBytesTo(self.ByteSize, "GB"),
             FromBytesTo(self.ByteSize, "TB"),
             TGM[0],
             TGM[1]
            ])
        return self.PropertiesCache
    
    def NameFromTokens(self, tokens):
        name = ""
        properties = self.GetProperties()
        for i in tokens:
            if isinstance(i, str):
                name += i
            if isinstance(i, int):
                name += properties.ByIndex(i)
        return name

    def Rename(self, path, tokens):
        newName = self.NameFromTokens(tokens)
        if newName == self.Name + self.Extension:
            return True

        fullNewName = os.path.join(path, newName)
        if os.path.isfile(fullNewName):
            NNS = os.path.splitext(newName)
            i = 1
            while os.path.isfile(os.path.join(path, f"{NNS[0]} ({i}){NNS[1]}")):
                i += 1
            newName = f"{NNS[0]} ({i}){NNS[1]}"
            fullNewName = os.path.join(path, newName)
        
        #Renaming file
        try:
            os.rename(os.path.join(path, self.Name + self.Extension), fullNewName)
            SetNewName = os.path.splitext(newName)
            self.Name = SetNewName[0]
            self.Extension = SetNewName[1]
        except OSError as e:
            return False
        
        self.PropertiesCache = None
        return True

class FileProperties:
     def __init__(self, properties: list):
          self.Properties = properties
     def ByName(self, name: str):
          return self.Properties[ValidInserts.index(name)]
     def ByIndex(self, index: int):
          return self.Properties[index]
          
#Directory class
class DirObj:
    def __init__(self, path, CreateTree = True):
        if not os.path.isdir(path):
             raise ValueError("Invalid directory path")
        
        self.Path = path
        
        self.UpdateFiles()
        self.EditLimit = len(self.Files)

        if CreateTree:
            self.UpdateDirs()

    def UpdateFiles(self):
        self.Files = []
        for i in os.scandir(self.Path):
             if i.is_file():
                  self.Files.append(FileObj(i.path))

    def UpdateDirs(self):
        self.Dirs = []
        for i in os.scandir(self.Path):
             if i.is_dir():
                self.Dirs.append(DirObj(i.path, True))

    def PrintOut(self, Order):
        print(" " * (Order - 1) + "╚" + str(os.path.basename(self.Path)))
        for i in self.Files:
            print(" " * Order + "╚" + i.Name + i.Extension)
        for i in self.Dirs:
            i.PrintOut(Order + 1)
            
    def SortFiles(self, sortBy: str, reversed: bool = False, filter: FileFilter = None, children: bool = True):
        toSort = []
        toNotSort = []
        for i in self.Files:
            if filter.MustInclude(i.GetProperties()):
                toSort.append(i)
            else:
                toNotSort.append(i)


        toSort.sort(key=lambda f: f.GetProperties().ByName(sortBy), reverse = reversed)

        self.EditLimit = len(toSort)
        self.Files = toSort + toNotSort

        if children:
            for i in self.Dirs:
                i.SortFiles(sortBy, reversed, filter, True)
    
    def RenameFiles(self, tokens: list, children: bool = True):
        for i in range(self.EditLimit):
            if not self.Files[i].Rename(self.Path, tokens):
                return False
        if children:
            for i in self.Dirs:
                i.RenameFiles(tokens)

    def GroupFiles(self, grouper: FileGrouper, mustArchive = False, children: bool = True):
        groupDirs = []
        for i in range(self.EditLimit):
            #Creating new name
            dirName = grouper.GetDirName(self.Files[i].GetProperties)

            #Adding to directory, if directory is not creating it
            if not os.path.isdir(os.path.join(self.Path, dirName)):
                os.makedirs(os.path.join(self.Path, dirName))
                groupDirs.append(dirName)
            shutil.move(os.path.join(self.Path, i.Name + i.Extension), os.path.join(self.Path, dirName, i.Name + i.Extension))

        #Repeating in children
        if children and hasattr(self, "Dirs"):
            for i in self.Dirs:
                i.GroupFiles(grouper, mustArchive, True)
        
        if self.EditLimit == len(self.Files):
            self.Files = []
        else:
            self.Files = self.Files[self.EditLimit:]
        
        for i in groupDirs:
            #Archiving new dirs if needed
            if mustArchive:
                fullDirPath = os.path.join(self.Path, i)
                #Getting dir's files
                dirFiles = []
                for j in os.listdir(fullDirPath):
                    if os.path.isfile(os.path.join(fullDirPath, j)):
                        dirFiles.append(j)

                #Adding all files to archive
                with zipfile.ZipFile(fullDirPath + ".zip", 'w') as Zip:
                    for j in dirFiles:
                        Zip.write(os.path.join(fullDirPath, j), os.path.join(i,j))

                #Adding zip to files
                self.Files.append(FileObj(fullDirPath + ".zip"))
                
                #Removing the dir (because it is already archived)
                shutil.rmtree(fullDirPath)
            else:
                if not hasattr(self, "Dirs"):
                    self.Dirs = []
                self.Dirs.append(DirObj(os.path.join(self.Path, i), True))

    def Flatten(self, Root = True):
        FilePaths = []
        
        for i in self.Dirs:
            FilePaths.extend(i.Flatten(False))
        
        if not Root:
            for i in self.Files:
                FilePaths.append(os.path.join(self.Path, i.Name + i.Extension))
        
            return FilePaths
        else:
            for i in FilePaths:
                shutil.move(i, os.path.join(self.Path, os.path.basename(i)))
            for i in self.Dirs:
                shutil.rmtree(i.Path)

#File grouping classes
class FileGrouper(abc.ABC):
     @abc.abstractmethod
     def GetDirName(self, properties: FileProperties) -> str: pass

class GroupByDate(FileGrouper):
     def __init__(self, dateAccuracy):
          self.Accuracy = dateAccuracy
    
     def GetDirName(self, properties: FileProperties) -> str:
          r = properties.ByName("year")
          if self.Accuracy > 0:
               r = f"{properties.ByName("month")}.{r}"
          if self.Accuracy > 1:
               r = f"{properties.ByName("day")}.{r}"
          return r

class GroupByExtension(FileGrouper):
     def __init__(self):
          pass
     def GetDirName(self, properties: FileProperties) -> str:
          return properties.ByIndex(2)

class GroupFilesBySize(FileGrouper):
     def __init__(self, size: int, measure: str):
          self.Size = size
          self.Measure = measure
     def GetDirName(self, properties: FileProperties) -> str:
          amount = properties.ByName(self.Measure) // self.Size
          bottom = amount * self.Size
          top = (amount + 1) * self.Size
          return f"{bottom}-{top}{self.Measure}"
          

#File filter classes
class FileFilter(abc.ABC):
	@abc.abstractmethod
	def MustInclude(self, properties: FileProperties) -> bool: pass
	
	@abc.abstractmethod
	def PrintOut(self) -> str: pass

class ExtensionFilter(FileFilter):
    def __init__(self, ext):
        if not ext[0] == ".":
             ext = "." + ext
        self.Extension = ext
          
    def MustInclude(self, properties: FileProperties) -> bool:
        if properties.ByIndex(2) == self.Extension: return True
        return False

    def PrintOut(self) -> str: return "Расширение " + self.Extension

class NameIncludesFilter(FileFilter):
    def __init__(self, word):
        self.Word = word
        self.FirstSymbol = word[0]
        self.Len = len(word)
          
    def MustInclude(self, properties: FileProperties) -> bool:
        name = properties.ByIndex(1)
        nameLen = len(name)
        
        for i in range(0, nameLen):
            if nameLen - i < self.Len: return False
            if name[i] == self.FirstSymbol:
                 if name[i:i+self.Len-1] == self.Word:
                    return True
	
    def PrintOut(self) -> str: return "Имя содержит " + self.Word

class SizeFilter(FileFilter):
    def __init__(self, compareMode, size, sizeMeasure):
        self.Comparison = compareMode
        self.Size = ToBytes(size, sizeMeasure)

    def MustInclude(self, properties: FileProperties) -> bool:
        if ComparisonOperators[self.Comparison](properties.ByName("bytes"), self.Size): return True
        return False
	
    def PrintOut(self): return "Размер {} чем {}".format(ComparisonName[self.Comparison], ToGreatestMeasure(self.Size))

###FUNCTIONS
def TryParseName(formula: str):
    nameTokens = []
    currentText = ""
    currentInsert = ""
    ParsingInsert = False
    for i in formula:
        if i == "<":
            if ParsingInsert:
                return False
            else:
                nameTokens.append(currentText)
                currentText = ""
                ParsingInsert = True
        elif i == ">":
            if not ParsingInsert:
                return False
            else:
                if not currentInsert in ValidInserts:
                    return False
                else:
                    nameTokens.append(ValidInserts.index(currentInsert))
                    currentInsert = ""
                    ParsingInsert = False
        else:
            if ParsingInsert:
                currentInsert += i
            else:
                currentText += i
    nameTokens.append(currentText)

    if ParsingInsert:
        return False
    return nameTokens


def ToBytes(size, measure):
    if measure in SizeMeasures:
        count = SizeMeasures.index(measure)
        return int(size * 1024 ** count)
    else:
        return False

def FromBytesTo(size, measure):
    if measure in SizeMeasures:
        count = SizeMeasures.index(measure)
        return round((size / 1024 ** count), 3)
    else:
        return False

def ToGreatestMeasure(bytes: int):
	count = 0
	current = bytes
	next = bytes / 1024
	
	while next >= 1 and count < len(SizeMeasures):
		count += 1
		current = next
		next = current / 1024
	
	if count >= len(SizeMeasures):
		return "Too big!~"
	else:
		return [str(round(current, 3)), SizeMeasures[count]]
     
###CONSTANTS
"""
0 - >
1 - <
2 - >=
3 - <=
4 - ==
5 - !=
"""
ComparisonOperators = {
	0 : operator.gt,
	1 : operator.lt,
	2 : operator.ge,
	3 : operator.le,
	4 : operator.eq,
	5 : operator.ne
}
ComparisonName = {0 : "больше", 1 : "меньше", 2 : "больше или равен", 3 : "меньше или равен", 4 : "равен", 5 : "не равен"}

#Names of inserts must be added here and their values must be added to GetVar method
ValidInserts = ["num", "name", "ext", "day", "month", "year", "bytes", "KB", "MB", "GB", "TB", "gsize", "gsizename"]

SizeMeasures = ["bytes", "KB", "MB", "GB", "TB"]