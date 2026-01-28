#Convenient stuff
from enum import IntEnum
import abc
import operator
#File work
import os
import shutil
import zipfile
#Date work
import datetime

###ENUMS
class Operators(IntEnum):
    Greater = 0
    Less = 1
    GreaterOrEqual = 2
    LessOrEqual = 3
    Equal = 4
    NotEqual = 5

class Languages(IntEnum):
    EN = 0
    RU = 1

class SizeMeasures(IntEnum):
    bytes = 0
    KB = 1
    MB = 2
    GB = 3
    TB = 4

class DateElements(IntEnum):
    Year = 0
    Month = 1
    Day = 2

###CONSTANTS
"""
0 - >
1 - <
2 - >=
3 - <=
4 - ==
5 - !=
"""
DateMeasuresNames = {
    Languages.EN: {
        DateElements.Year: "years",
        DateElements.Month: "months",
        DateElements.Day: "days"
    },
    Languages.RU: {
        DateElements.Year: "годов",
        DateElements.Month: "месяцов",
        DateElements.Day: "дней"
    }
}
ComparisonName = {
    Languages.EN: {
        Operators.Greater: "greater than",
        Operators.Less: "less than",
        Operators.GreaterOrEqual: "greater than or equal",
        Operators.LessOrEqual: "less than or equal",
        Operators.Equal: "equal",
        Operators.NotEqual: "not equal"
    },
    Languages.RU: {
        Operators.Greater: "больше",
        Operators.Less: "меньше",
        Operators.GreaterOrEqual: "больше или равен",
        Operators.LessOrEqual: "меньше или равен",
        Operators.Equal: "равен",
        Operators.NotEqual: "не равен"
    }
}
ComparisonOperators = {
	Operators.Greater: operator.gt,
	Operators.Less: operator.lt,
	Operators.GreaterOrEqual: operator.ge,
	Operators.LessOrEqual: operator.le,
	Operators.Equal: operator.eq,
	Operators.NotEqual: operator.ne
}
MeasuresNames = [
    "bytes",
    "KB",
    "MB",
    "GB",
    "TB"
]
GreatestMeasure = 4

###FUNCTIONS
def TryParseName(formula: str):
    fileProperties = FileProperties()

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
                try:
                    number = fileProperties.ByName(currentInsert)
                    nameTokens.append(number)
                    currentInsert = ""
                    ParsingInsert = False
                except:
                    return False
        else:
            if ParsingInsert:
                currentInsert += i
            else:
                currentText += i
    nameTokens.append(currentText)

    if ParsingInsert:
        return False
    return nameTokens

def ToBytes(size, measure: SizeMeasures) -> int:
    return int(size * 1024 ** measure)

def FromBytesTo(size: int, measure: SizeMeasures):
    return round((size / 1024 ** measure), 3)

def ToGreatestMeasure(bytes: int):
	count = 0
	current = bytes
	next = bytes / 1024
	
	while next >= 1 and count <= GreatestMeasure:
		count += 1
		current = next
		next = current / 1024
	
	if count > GreatestMeasure:
		return "Too big!~"
	else:
		return [str(round(current, 3)), count]

###CLASSES
#File class
class FileObj:
    def __init__(self, path):
        if os.path.isfile(path):
            self.UpdateData(path)
            self.Number = 0
        else:
            raise ValueError("Invalid file path")
    
    def UpdateData(self, path):
        NameAndExt = os.path.splitext(os.path.basename(path))
        self.Name = NameAndExt[0]
        self.Extension = NameAndExt[1]

        self.MDate = os.path.getmtime(path)
        
        self.ByteSize = os.path.getsize(path)

        self.PropertiesCache = None
        
    def Day(self):
        return datetime.datetime.fromtimestamp(self.MDate).strftime("%d")
    def Month(self):
        return datetime.datetime.fromtimestamp(self.MDate).strftime("%m")
    def Year(self):
        return datetime.datetime.fromtimestamp(self.MDate).strftime("%Y")
    
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
             FromBytesTo(self.ByteSize, 1),
             FromBytesTo(self.ByteSize, 2),
             FromBytesTo(self.ByteSize, 3),
             FromBytesTo(self.ByteSize, 4),
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
     def __init__(self, properties: list | None = None):
          if properties == None:
              properties = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
          self.Properties = properties
     ValidInserts = ["num", "name", "ext", "day", "month", "year", "bytes", "KB", "MB", "GB", "TB", "gsize", "gsizename"]
     def ByName(self, name: str):
          return self.Properties[self.ValidInserts.index(name)]
     def ByIndex(self, index: int):
          return self.Properties[index]

#File filter classes
class IFileFilter(abc.ABC):
	@abc.abstractmethod
	def MustInclude(self, properties: FileProperties) -> bool: pass
	@abc.abstractmethod
	def PrintOut(self, lang: Languages) -> str: pass

class NumberFilter(IFileFilter):
    def __init__(self, compareMode: Operators, num: int):
        self.Comparison = compareMode
        self.Number = num
    
    def MustInclude(self, properties: FileProperties) -> bool:
        return ComparisonOperators[self.Comparison](properties.ByIndex(0),self.Number)
    
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"number is {ComparisonName[Languages.EN][self.Comparison]} {self.Number}"
        if lang == Languages.RU:
            r = f"номер {ComparisonName[Languages.RU][self.Comparison]} {self.Number}"
        return r

class NameIncludesFilter(IFileFilter):
    def __init__(self, word: str):
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
	
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"Name includes {self.Word}"
        if lang == Languages.RU:
            r = f"Имя содержит {self.Word}"
        return r

class ExtensionFilter(IFileFilter):
    def __init__(self, ext: str):
        if not ext[0] == ".":
             ext = "." + ext
        self.Extension = ext
          
    def MustInclude(self, properties: FileProperties) -> bool:
        if properties.ByIndex(2) == self.Extension: return True
        return False

    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"Extension is {self.Extension}"
        if lang == Languages.RU:
            r = f"Расширение {self.Extension}"
        return r

class DateFilter(IFileFilter):
    def __init__(self, compareMode: Operators, day: int, month: int, year: int):
        self.Comparison = compareMode
        self.DatetimeObj = datetime.datetime(year, month, day)
    
    def MustInclude(self, properties: FileProperties) -> bool:
        return ComparisonOperators[self.Comparison](datetime.datetime(properties.ByName("year"), properties.ByName("month"), properties.ByName("day")), self.DatetimeObj)
    
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"date is {ComparisonName[Languages.EN][self.Comparison]} {self.DatetimeObj.strftime('%d.%m.%Y')}"
        if lang == Languages.RU:
            r = f"дата {ComparisonName[Languages.RU][self.Comparison]} {self.DatetimeObj.strftime('%d.%m.%Y')}"
        return r

class SizeFilter(IFileFilter):
    def __init__(self, compareMode: Operators, size, sizeMeasure: SizeMeasures):
        self.Comparison = compareMode
        self.Size = ToBytes(size, sizeMeasure)

    def MustInclude(self, properties: FileProperties) -> bool:
        if ComparisonOperators[self.Comparison](properties.ByName("bytes"), self.Size): return True
        return False
	
    def PrintOut(self, lang: Languages) -> str:
        r = ""

        GM = ToGreatestMeasure(self.Size)
        sizeText = ""

        if GM is list:
            sizeText = f"{GM[0]} {MeasuresNames[GM[1]]}"
        else:
            sizeText = GM
        
        if lang == Languages.EN:
            r = f"size is {ComparisonName[Languages.EN][self.Comparison]} {sizeText}"
        if lang == Languages.RU:
            r = f"размер {ComparisonName[Languages.RU][self.Comparison]} {sizeText}"
        
        return r

class NotFilter(IFileFilter):
    def __init__(self, filter: IFileFilter):
        self.Filter = filter
    
    def MustInclude(self, properties: FileProperties) -> bool:
        return not self.Filter.MustInclude(properties)
    
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        
        if lang == Languages.EN:
            r = "not " + self.Filter.PrintOut(Languages.EN)
        if lang == Languages.RU:
            r = "не " + self.Filter.PrintOut(Languages.RU)
        
        return r

#File grouping classes
class IFileGrouper(abc.ABC):
     @abc.abstractmethod
     def GetDirName(self, properties: FileProperties) -> str: pass
     @abc.abstractmethod
     def PrintOut(self, lang: Languages) -> str: pass

class NumberGrouper(IFileGrouper):
    def __init__(self, range: int):
        self.Range = range
    
    def GetDirName(self, properties: FileProperties) -> str:
        amount = properties.ByIndex(0) // self.Range
        bottom = amount * self.Range
        top = (amount + 1) * self.Range
        return f"{bottom}-{top}"
    
    def PrintOut(self, lang) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"by number, in range of {self.Range}"
        if lang == Languages.RU:
            r = f"по номеру, в диапазоне {self.Range}"
        return r

class ExtensionGrouper(IFileGrouper):
     def __init__(self):
          pass
     
     def GetDirName(self, properties: FileProperties) -> str:
          return properties.ByIndex(2)
     
     def PrintOut(self, lang: Languages) -> str:
         if lang == Languages.EN:
             return "by extension"
         if lang == Languages.RU:
             return "по расширению"

class DateGrouper(IFileGrouper):
     def __init__(self, dateAccuracy: DateElements):
          self.Accuracy = dateAccuracy
    
     def GetDirName(self, properties: FileProperties) -> str:
          r = properties.ByName("year")
          if self.Accuracy > 0:
               r = f"{properties.ByName('month')}.{r}"
          if self.Accuracy > 1:
               r = f"{properties.ByName('day')}.{r}"
          return r
     
     def PrintOut(self, lang: Languages) -> str:
         r = ""
         if lang == Languages.EN:
             r = f"by date with accuracy up to {DateMeasuresNames[Languages.EN][self.Accuracy]}"
         if lang == Languages.RU:
             r = f"по дате с точностью до {DateMeasuresNames[Languages.RU][self.Accuracy]}"
         return r

class SizeGrouper(IFileGrouper):
     def __init__(self, size: int, measure: str):
          self.Size = size
          self.Measure = measure
          
     def GetDirName(self, properties: FileProperties) -> str:
          amount = properties.ByName(self.Measure) // self.Size
          bottom = amount * self.Size
          top = (amount + 1) * self.Size
          return f"{bottom}-{top}{self.Measure}"
     
     def PrintOut(self, lang: Languages) -> str:
         r = ""
         GM = ToGreatestMeasure(self.Size)
         sizeText = ""
         
         if GM is str:
             sizeText = GM
         else:
             sizeText = f"{GM[0]} {MeasuresNames[GM[1]]}"
         
         if lang == Languages.EN:
             r = f"by size, in range of {sizeText}"
         if lang == Languages.RU:
             r = f"по размеру, в диапазоне {sizeText}"
         return r

#Directory class
class DirObj:
    def __init__(self, path: str, CreateTree: bool = True):
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
            
    def SortFiles(self, sortBy: str, reversed: bool = False, filter: IFileFilter = None, children: bool = True):
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

    def GroupFiles(self, grouper: IFileGrouper, mustArchive: bool = False, children: bool = True):
        groupDirs = []
        for i in range(self.EditLimit):
            #Creating new name
            currentFile = self.Files[i]
            currentProp = currentFile.GetProperties()
            dirName = grouper.GetDirName(currentFile.GetProperties())

            #Adding to directory, if directory is not creating it
            if not os.path.isdir(os.path.join(self.Path, dirName)):
                os.makedirs(os.path.join(self.Path, dirName))
                groupDirs.append(dirName)
            shutil.move(os.path.join(self.Path, currentProp.ByName("name") + currentProp.ByName("ext")), os.path.join(self.Path, dirName, currentProp.ByName("name") + currentProp.ByName("ext")))

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

#Command classes
class ICommand(abc.ABC):
    @abc.abstractmethod
    def Execute(self, dirObj: DirObj) -> None: pass
    @abc.abstractmethod
    def PrintOut(self, lang: Languages) -> str: pass

class SortCommand(ICommand):
    def __init__(self, sortBy: str, reversedSort: bool = False, filter: IFileFilter = None, children: bool = True):
        try:
            prop = FileProperties()
            prop.ByName(sortBy)
        except:
            raise ValueError("Invalid sort by parameter")
        self.SortBy = sortBy
        self.Reverse = reversedSort
        self.Filter = filter
        self.Children = children
    
    def Execute(self, dirObj: DirObj):
        dirObj.SortFiles(self.SortBy, self.Reverse, self.Filter, self.Children)
    
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"Sort files for further work, sort by parameter {self.SortBy}{', reversed sorting,' if self.Reverse else ''}{', include files if '+ self.Filter.PrintOut(Languages.EN)}{', repeat in children' if self.Children else ''}"
        if lang == Languages.RU:
            r = f"Сортировать файлы для поледующей работы, сортировать по параметру {self.SortBy}{', обратная сортировка' if self.Reverse else ''}{', включать файлы если '+ self.Filter.PrintOut(Languages.RU)}{', повторить в дочерних директориях' if self.Children else ''}"
        return r

class RenameCommand(ICommand):
    def __init__(self, nameFormula: str, children: bool = True):
        tokens = TryParseName(nameFormula)
        if tokens == False:
            raise ValueError("Invalid name formula")
        self.Formula = nameFormula
        self.Tokens = tokens
        self.Children = children
    
    def Execute(self, dirObj: DirObj):
        dirObj.RenameFiles(self.Tokens, self.Children)
    
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"Rename files by formula {self.Formula}{', repeat in children' if self.Children else ''}"
        if lang == Languages.RU:
            r = f"Переименовать файлы по формуле {self.Formula}{', повторить в дочерних директориях' if self.Children else ''}"
        return r

class GroupCommand(ICommand):
    def __init__(self, grouper: IFileGrouper, mustArchive: bool = False, children: bool = True):
        self.Grouper = grouper
        self.MustArchive = mustArchive
        self.Children = children
    
    def Execute(self, dirObj: DirObj):
        dirObj.GroupFiles(self.Grouper, self.MustArchive, self.Children)
    
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = f"Group files {self.Grouper.PrintOut(Languages.EN)}{', archive' if self.MustArchive else ''}{', repeat in children' if self.Children else ''}"
        if lang == Languages.RU:
            r = f"Сгруппировать файлы {self.Grouper.PrintOut(Languages.RU)}{', архивировать' if self.MustArchive else ''}{', повторить в дочерних директориях' if self.Children else ''}"
        return r

class FlattenCommand(ICommand):
    def __init__(self):
        pass

    def Execute(self, dirObj: DirObj):
        dirObj.Flatten()
    
    def PrintOut(self, lang: Languages) -> str:
        r = ""
        if lang == Languages.EN:
            r = "Flatten tree"
        if lang == Languages.RU:
            r = "Сгладить дерево"
        return r