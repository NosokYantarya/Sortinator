#Convenient stuff
from enum import Enum
import abc
import operator
#Work with files
import os
from os.path import *
import shutil
import zipfile
#Work with files
from datetime import datetime
#GUI
from tkinter import *
from tkinter import ttk
from tkinter import filedialog



###CLASSES
#File class
class FileObj:
    def __init__(self, path):
        if isfile(path):
            self.UpdateData(path)
        else:
            return None

    def UpdateData(self, path):
        NameAndExt = splitext(basename(path))
        self.Name = NameAndExt[0]
        self.Extension = NameAndExt[1]

        self.MDate = os.path.getmtime(path)
        
        self.ByteSize = os.path.getsize(path)
        
    def Day(self):
        return datetime.fromtimestamp(self.MDate).strftime("%d")
    def Month(self):
        return datetime.fromtimestamp(self.MDate).strftime("%m")
    def Year(self):
        return datetime.fromtimestamp(self.MDate).strftime("%Y")
    
    def GetVar(self, var):
        #["num", "name", "ext", "day", "month", "year", "bytes", "kb", "mb", "gb", "tb", "gsize", "gsizename"]
        getVar = [
            lambda: self.Number,
            lambda: self.Name,
            lambda: self.Extension,
            lambda: self.Day(),
            lambda: self.Month(),
            lambda: self.Year(),
            lambda: self.ByteSize,
            lambda: FromBytesTo(self.ByteSize, "KB"),
            lambda: FromBytesTo(self.ByteSize, "MB"),
            lambda: FromBytesTo(self.ByteSize, "GB"),
            lambda: FromBytesTo(self.ByteSize, "TB"),
            lambda: ToGreatestMeasure(self.ByteSize)[0],
            lambda: ToGreatestMeasure(self.ByteSize)[1]
        ]

        if var in ValidInserts:
            return getVar[var]
        else:
            return False
    
    def NameFromTokens(self, tokens):
        name = ""
        for i in tokens:
            if type(i) == str:
                name += i
            if type(i) == int:
                name += self.GetVar(i)
        return name

    def Rename(self, path, tokens):
        newName = self.NameFromTokens(tokens)
        if newName == self.Name + self.Extension:
            return True

        fullName = join(path, newName)
        if isfile(fullName):
            NNS = splitext(newName)
            i = 1
            while isfile(join(path, NNS[0] + "(" + str(i) + ")" + NNS[1])):
                i += 1
            NewName = NNS[0] + "(" + str(i) + ")" + NNS[1]

        #Renaming file
        try:
            os.rename(join(path, self.Name + self.Extension), fullName)
            SetNewName = splitext(NewName)
            self.Name = SetNewName[0]
            self.Extension = SetNewName[1]
            
        except BaseException as e:
            return False
            
        return True

#Directory class
class DirObj:
    def __init__(self, Path, CreateTree):
        
        self.Path = Path
        
        self.UpdateFiles()

        if CreateTree:
            self.UpdateDirs()

    def UpdateFiles(self):
        self.Files = []

        for i in os.listdir(self.Path):
            if isfile(join(self.Path, i)):
                self.Files.append(FileObj(join(self.Path, i)))

    def UpdateDirs(self):
        self.Dirs = []
        Dirs = []
        for i in os.listdir(self.Path):
            if isdir(join(self.Path, i)):
                self.Dirs.append(DirObj(join(self.Path, i), True))

    def PrintOut(self, Order):
        print(" " * (Order - 1) + "╚" + str(os.path.basename(self.Path)))
        for i in self.Files:
            print(" " * Order + "╚" + i.Name + i.Extension)
        for i in self.Dirs:
            i.PrintOut(Order + 1)
            
    def RenameFiles(self, NameFormula):
        for i in self.Files:
            if not i.Rename(self.Path, NameFormula):
                return False
        if hasattr(self, "Dirs"):
            for i in self.Dirs:
                i.RenameFiles(NameFormula)

    def SortFiles(self, SortingType, Reversed):
        FileTuples = []
        #0: sort by extension
        if SortingType == 0:
            for i in self.Files:
                FileTuples.append((i.Extension, i))
        #1: sort by mtime
        if SortingType == 1:
            for i in self.Files:
                FileTuples.append( ( getmtime(join(self.Path, i.Name + i.Extension)), i ) )
        FileTuples.sort(key = lambda x: x[0], reverse = Reversed)
        

        NewFiles = []
        for i, (_, file) in enumerate(FileTuples):
            file.Number = i + 1
            NewFiles.append(file)


        self.Files = NewFiles

        if hasattr(self, "Dirs"):
            for i in self.Dirs:
                i.SortFiles(SortingType, Reversed)

    def GroupFiles(self, GroupingType, MustArchive):
        GroupDirs = []

        for i in self.Files:
            #Creating new name
            DirName = ""
            if GroupingType == 0:
                DirName = i.Extension
            else:
                DirName = i.Year
                if GroupingType < 4:
                    DirName = "{}.{}".format(i.Month, DirName)
                if GroupingType < 3:
                    DirName = "{}.{}".format(i.Day, DirName)

            #Adding to directory, if directory is not creating it
            if not os.path.isdir(join(self.Path, DirName)):
                os.makedirs(join(self.Path, DirName))
                GroupDirs.append(DirName)
            shutil.move(join(self.Path, i.Name + i.Extension), join(self.Path, DirName, i.Name + i.Extension))

        self.Files = []

        #Repeating in children
        if hasattr(self, "Dirs"):
            for i in self.Dirs:
                i.GroupFiles(GroupingType, MustArchive)

        
        for i in GroupDirs:
            #Archiving new dirs if needed
            if MustArchive:
                #Getting dir's files
                Files = []
                for j in os.listdir(join(self.Path, i)):
                    if isfile(join(self.Path, i, j)):
                        Files.append(j)

                #Adding all files to archive
                with zipfile.ZipFile(join(self.Path, i + ".zip"), 'w') as Zip:
                    for j in Files:
                        Zip.write(join(self.Path, i, j), join(i,j))

                #Adding zip to files
                self.Files.append(FileObj(join(self.Path, i + ".zip")))
                
                #Removing the dir (because it is already archived)
                shutil.rmtree(join(self.Path, i))
            else:
                if not hasattr(self, "Dirs"):
                    self.Dirs = []
                self.Dirs.append(DirObj(join(self.Path, i), True))

    def Flatten(self, Root = True):
        FilePaths = []
        
        for i in self.Dirs:
            FilePaths.extend(i.Flatten(False))
        
        if not Root:
            for i in self.Files:
                FilePaths.append(join(self.Path, i.Name + i.Extension))
        
            return FilePaths
        else:
            for i in FilePaths:
                shutil.move(i, join(self.Path, basename(i)))
            for i in self.Dirs:
                shutil.rmtree(i.Path)
            

###FUNCTIONS
#Backend stuff
#Names of inserts must be added here and their values must be added to GetVar method
ValidInserts = ["num", "name", "ext", "day", "month", "year", "bytes", "kb", "mb", "gb", "tb", "gsize", "gsizename"]
def TryParseName(formula):
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

SizeMeasures = ["bytes", "KB", "MB", "GB", "TB"]
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

def ToGreatestMeasure(bytes):
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


#GUI stuff
#For updating GUI when something is pressed
def UpdateGUI():
    FlattenActCheck.pack_forget()
    
    RenamingFull.pack_forget()
    GroupingFull.pack_forget()
    DateGroupTypeFrame.pack_forget()
    FlatFull.pack_forget()
    OutFull.pack_forget()

    if SortChildren.get():
        FlattenActCheck.pack(side = LEFT)
    
    if MustRename.get():
        RenamingFull.pack(pady = 5)

    if MustGroup.get():
        GroupingFull.pack(pady = 5)

    if GroupingType.get() == 1:
        DateGroupTypeFrame.pack()

    if MustFlatten.get() and SortChildren.get():
        FlatFull.pack(pady = 5)
    
    OutFull.pack(pady = 5)
#Directory select function
def DirSel():
    Path = filedialog.askdirectory(title = "Выбор папки", initialdir = "/")
    DirSelEntry.delete(0, END)
    DirSelEntry.insert(0, Path)
#Write something in a bottom text
def Output(Out):
    OutTxt.configure(text = Out)


#Full function
def Execute():
    Output("Выполняется")
    
    #Creating dir object
    Path = DirSelEntry.get()
    if not isdir(Path):
        Output("Невалидная директория")
        return False
    DirObject = DirObj(Path, SortChildren.get())

    MF = MustFlatten.get()
    FBOA = FlattenBeforeOrAfter.get()
    SC = SortChildren.get()
    
    #Flattening if needed
    if MF and FBOA and SC:
        DirObject.Flatten()

    #Renaming
    NF = NameEntry.get()
    if MustRename.get():
        if TryParseName(NF) != False:
            DirObject.SortFiles(FileNumeration.get(), ReverseSort.get())
            DirObject.RenameFiles(NF)
        else:
            Output("Невалидное имя файла")
            return False

    #Grouping
    if MustGroup.get():
        GT = GroupingType.get()
        DGT = DateGroupType.get()
        MA = MustArchive.get()
        if GT == 0:
            DirObject.GroupFiles(0, MA)
        else:
            DirObject.GroupFiles(DGT, MA)

    #Flattening if needed
    if MF and not FBOA and SC:
        DirObject.Flatten()

    Output("Выполнено успешно")
    return True



###WINDOW
#Window init
Window=Tk()
Window.title('Sortinator')
Window.geometry("500x500")



###VARIABLES

#Settings values
#Actions that must be done
MustRename = BooleanVar(value = False)
MustGroup = BooleanVar(value = False)
MustFlatten = BooleanVar(value = False)

#Other general settings
SortChildren = IntVar(value = 0)

#Renaming settings
FileNumeration = IntVar(value = 0)
ReverseSort = BooleanVar(value = False)

#Grouping settings
GroupingType = IntVar(value = 0)
DateGroupType = IntVar(value = 1)
MustArchive = BooleanVar(value = False)

#Flattening settings
FlattenBeforeOrAfter = BooleanVar(value = False)



###GUI
WindowFrame = Frame(Window)
WindowFrame.pack(padx = 10, pady = 5)

#General settings
GeneralFull = Frame(WindowFrame)
GeneralFull.pack()

GenTitle = Label(GeneralFull, text = "Основные настройки", font=("Arial", 10, "bold"))
GenTitle.pack()

#Directory select
DirSelFull = Frame(GeneralFull)
DirSelFull.pack()

DirSelTxt = Label(DirSelFull, text = "Выберите папку:")
DirSelTxt.pack(side = TOP)

DirSelFrame = Frame(DirSelFull)
DirSelFrame.pack(side = TOP)

DirSelButton = Button(DirSelFrame, text="Обзор", command = DirSel)
DirSelButton.pack(side = RIGHT)

DirSelEntry = Entry(DirSelFrame, width = 75)
DirSelEntry.pack(side = RIGHT)

#Action select
ActSelFull = Frame(GeneralFull)
ActSelFull.pack()

ActSelTxt = Label(ActSelFull, text = "Что нужно сделать?")
ActSelTxt.pack()

ActSelFrame = Frame(ActSelFull)
ActSelFrame.pack()

RenameActCheck = Checkbutton(ActSelFrame, text = "Переименовать", var = MustRename, command = UpdateGUI)
RenameActCheck.pack(side = LEFT)

GroupActCheck = Checkbutton(ActSelFrame, text = "Сгруппировать", var = MustGroup, command = UpdateGUI)
GroupActCheck.pack(side = LEFT)

FlattenActCheck = Checkbutton(ActSelFrame, text = "Сгладить дерево", var = MustFlatten, command = UpdateGUI)

#Children select
ChildSelFull = Frame(GeneralFull)
ChildSelFull.pack()

ChildCheck = Checkbutton(ChildSelFull, text = "Выполнять в дочерних папках", var = SortChildren, command = UpdateGUI)
ChildCheck.pack()


#Renaming settings
RenamingFull = Frame(WindowFrame)

RenameTitle = Label(RenamingFull, text = "Настройки переименования", font=("Arial", 10, "bold"))
RenameTitle.pack()

NameEntryTxt = Label(RenamingFull, text = "Введите формулу имени:")
NameEntryTxt.pack()

NameEntry = Entry(RenamingFull, width = 75)
NameEntry.pack()

NumberByTitle = Label(RenamingFull, text = "Нумеровать файлы по:")
NumberByTitle.pack()

#Number by
NumberByFrame = Frame(RenamingFull)
NumberByFrame.pack()

NumberByExt = Radiobutton(NumberByFrame,text = "По расширению", value = 0, variable = FileNumeration)
NumberByExt.pack(side = LEFT)

NumberByDate = Radiobutton(NumberByFrame,text = "По дате", value = 1, variable = FileNumeration)
NumberByDate.pack(side = LEFT)

NameReverseSortCheck = Checkbutton(RenamingFull, text = "Обратная сортировка", var = ReverseSort)
NameReverseSortCheck.pack()


#Grouping settings
GroupingFull = Frame(WindowFrame)

GroupingTitle = Label(GroupingFull, text = "Настройки группировки", font=("Arial", 10, "bold"))
GroupingTitle.pack()

#Grouping type select
GroupTypeFrame = Frame(GroupingFull)
GroupTypeFrame.pack()

GroupByExtButton = Radiobutton(GroupTypeFrame, text = "По расширению", value = 0, variable = GroupingType, command = UpdateGUI)
GroupByExtButton.pack(side = LEFT)

GroupByDateButton = Radiobutton(GroupTypeFrame, text = "По дате", value = 1, variable = GroupingType, command = UpdateGUI)
GroupByDateButton.pack(side = LEFT)

#Date grouping type select
DateGroupTypeFrame = Frame(GroupingFull)

GroupByDayButton = Radiobutton(DateGroupTypeFrame, text = "По дням", value = 1, variable = DateGroupType)
GroupByDayButton.pack(side = LEFT)

GroupByDayButton = Radiobutton(DateGroupTypeFrame, text = "По месяцам", value = 2, variable = DateGroupType)
GroupByDayButton.pack(side = LEFT)

GroupByDayButton = Radiobutton(DateGroupTypeFrame, text = "По годам", value = 3, variable = DateGroupType)
GroupByDayButton.pack(side = LEFT)

#Archiving check
MustArchiveCheck = Checkbutton(GroupingFull, text = "Архивировать", var = MustArchive)
MustArchiveCheck.pack()


#Flattening settings
FlatFull = Frame(WindowFrame)

FlatTitle = Label(FlatFull, text = "Настройки сглаживания", font=("Arial", 10, "bold"))
FlatTitle.pack()

BorATitle = Label(FlatFull, text = "Сгладить в начале или в конце")
BorATitle.pack()

#Flatten before or after
FlatBorAFrame = Frame(FlatFull)
FlatBorAFrame.pack()

FlattenBeforeButton = Radiobutton(FlatBorAFrame, text = "В начале", value = True, variable = FlattenBeforeOrAfter)
FlattenBeforeButton.pack(side = LEFT)

FlattenAfterButton = Radiobutton(FlatBorAFrame, text = "В конце", value = False, variable = FlattenBeforeOrAfter)
FlattenAfterButton.pack(side = LEFT)


#Button & output
OutFull = Frame(WindowFrame)
OutFull.pack(pady = 5)

SortButton = Button(OutFull, text = "Выполнить", command = Execute)
SortButton.pack()

OutTxt = Label(OutFull, text = "")
OutTxt.pack()



Window.mainloop()