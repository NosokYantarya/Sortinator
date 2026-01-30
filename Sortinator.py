import Filework
import sys
import json
from PyQt6 import QtCore, QtWidgets, QtGui



SaveDir = Filework.os.path.join(Filework.os.path.dirname(Filework.os.path.abspath(__file__)), "SavedPrograms")

class DirectorySelect(QtWidgets.QWidget):
    def __init__(self, height: int, buttonWidth: int, parent = None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.Layout = QtWidgets.QHBoxLayout(self)

        self.Entry = QtWidgets.QLineEdit()
        self.Entry.setFixedHeight(height)
        self.Layout.addWidget(self.Entry)

        self.BrowseButton = QtWidgets.QPushButton("Обзор")
        self.BrowseButton.clicked.connect(self.SelectDialogue)
        self.Layout.addWidget(self.BrowseButton)
        self.BrowseButton.setFixedSize(QtCore.QSize(buttonWidth, height))
    
    def SelectDialogue(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            ""
        )
        self.Entry.setText(directory)
    
    def GetPath(self) -> str:
        return self.Entry.text()


class CommandsDisplay(QtWidgets.QScrollArea):
    def __init__(self, height: int, parent = None):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setFixedHeight(height)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.InnerWidget = QtWidgets.QWidget()
        self.setWidget(self.InnerWidget)

        self.Layout = QtWidgets.QVBoxLayout(self.InnerWidget)
        self.Layout.addStretch()

        self.CommandWidgets = {}
        self.NextIndex = 0
    
    def AddCommand(self, command: Filework.ICommand):
        newWidget = CommandWidget(command, self.NextIndex, self, self.InnerWidget)
        self.Layout.addWidget(newWidget)

        self.CommandWidgets[self.NextIndex] = newWidget
        self.NextIndex += 1

        for i in range(self.Layout.count()):
            item = self.Layout.itemAt(i)
            if isinstance(item, QtWidgets.QSpacerItem):
                self.Layout.removeItem(item)
        self.Layout.addStretch()
    
    def RemoveCommand(self, index: int):
        if index in self.CommandWidgets:
            commandWidget = self.CommandWidgets[index]
            del self.CommandWidgets[index]
            self.Layout.removeWidget(commandWidget)
            commandWidget.deleteLater()
    
    def ClearCommands(self):
        keys = list(self.CommandWidgets.keys())
        for i in keys:
            self.RemoveCommand(i)

    def Execute(self, dirObj: Filework.DirObj):
        for i in self.CommandWidgets.values():
            i.Execute(dirObj)
    
    def GetSerialised(self):
        lst = []
        for i in self.CommandWidgets.values():
            lst.append(i.CommandObj.Serialised)
        return lst

class CommandWidget(QtWidgets.QWidget):
    def __init__(self, command: Filework.ICommand, index: int, display: CommandsDisplay, parent = None):
        super().__init__(parent)
        self.CommandObj = command
        self.index = index
        self.Display = display

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.RemoveButton = QtWidgets.QPushButton("Удалить")
        self.RemoveButton.clicked.connect(lambda: self.Display.RemoveCommand(self.index))
        self.RemoveButton.setFixedSize(QtCore.QSize(100, 30))
        self.Layout.addWidget(self.RemoveButton)

        self.CommandLabel = QtWidgets.QLabel(self.CommandObj.PrintOut(Filework.Languages.RU))
        self.Layout.addWidget(self.CommandLabel)
    
    def Execute(self, dirObj: Filework.DirObj):
        self.CommandObj.Execute(dirObj)


class IFileFilterMaker(QtWidgets.QWidget):
    def GetFilter(self) -> Filework.IFileFilter:
        raise NotImplementedError("Subclasses must implement GetFilter()")

class NumberFilterMaker(IFileFilterMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.ComparisonSelect = QtWidgets.QComboBox(self)
        self.ComparisonSelect.addItems([">", "<", ">=", "<=", "==", "!="])
        self.Layout.addWidget(self.ComparisonSelect)

        self.NumberEntry = QtWidgets.QLineEdit(self)
        self.NumberEntry.setValidator(QtGui.QIntValidator(0, 1000000, self))
        self.Layout.addWidget(self.NumberEntry)
    
    def GetFilter(self) -> Filework.IFileFilter: return Filework.NumberFilter(self.ComparisonSelect.currentIndex(), self.NumberEntry.text())

class NameIncludesFilterMaker(IFileFilterMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.Entry = QtWidgets.QLineEdit(self)
        self.Layout.addWidget(self.Entry)
    
    def GetFilter(self) -> Filework.IFileFilter: return Filework.NameIncludesFilter(self.Entry.text())

class ExtensionFilterMaker(IFileFilterMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.Entry = QtWidgets.QLineEdit(self)
        self.Layout.addWidget(self.Entry)
    
    def GetFilter(self) -> Filework.IFileFilter: return Filework.ExtensionFilter(self.Entry.text())

class DateFilterMaker(IFileFilterMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.ComparisonSelect = QtWidgets.QComboBox(self)
        self.ComparisonSelect.addItems([">", "<", ">=", "<=", "==", "!="])
        self.Layout.addWidget(self.ComparisonSelect)

        self.DayEntry = QtWidgets.QLineEdit(self)
        self.DayEntry.setValidator(QtGui.QIntValidator(1, 31, self))
        self.Layout.addWidget(self.DayEntry)

        self.MonthEntry = QtWidgets.QLineEdit(self)
        self.MonthEntry.setValidator(QtGui.QIntValidator(1, 12, self))
        self.Layout.addWidget(self.MonthEntry)

        self.YearEntry = QtWidgets.QLineEdit(self)
        self.Layout.addWidget(self.YearEntry)
    
    def GetFilter(self) -> Filework.IFileFilter: 
        d = int(self.DayEntry.text())
        m = int(self.MonthEntry.text())
        y = int(self.YearEntry.text())
        try:
            q = Filework.datetime.datetime(y, m, d)
            del q
        except:
            raise ValueError("Date Filter: invalid date input")
        return Filework.DateFilter(self.ComparisonSelect.currentIndex(), d, m, y)

class SizeFilterMaker(IFileFilterMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.ComparisonSelect = QtWidgets.QComboBox(self)
        self.ComparisonSelect.addItems([">", "<", ">=", "<=", "==", "!="])
        self.Layout.addWidget(self.ComparisonSelect)

        self.SizeNumberEntry = QtWidgets.QLineEdit(self)
        self.SizeNumberEntry.setValidator(QtGui.QDoubleValidator(0.0, 1024.0, 3, self))
        self.Layout.addWidget(self.SizeNumberEntry)

        self.SizeMeasureSelect = QtWidgets.QComboBox(self)
        self.SizeMeasureSelect.addItems(["bytes", "KB", "MB", "GB", "TB"])
        self.Layout.addWidget(self.SizeMeasureSelect)
    
    def GetFilter(self) -> Filework.IFileFilter: return Filework.SizeFilter(self.ComparisonSelect.currentIndex(), self.SizeNumberEntry.text(), self.SizeMeasureSelect.currentIndex())

class AnyFilterMaker(IFileFilterMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QVBoxLayout(self)

        self.Layout1 = QtWidgets.QHBoxLayout()
        self.Layout.addLayout(self.Layout1)

        self.TypeSelectLabel = QtWidgets.QLabel("Фильтр", self)
        self.Layout1.addWidget(self.TypeSelectLabel)

        self.TypeSelect = QtWidgets.QComboBox(self)
        self.TypeSelect.addItems(["Нет", "Номер", "Название содержит", "Расширение", "Дата", "Размер"])
        self.TypeSelect.currentIndexChanged.connect(self.ChangeType)
        self.Layout1.addWidget(self.TypeSelect)

        self.Layout2 = QtWidgets.QHBoxLayout()
        self.Layout.addLayout(self.Layout2)

        self.NotCheckbox = QtWidgets.QCheckBox("Не", self)
        self.Layout2.addWidget(self.NotCheckbox)

        self.FilterMakers = [NumberFilterMaker(self), NameIncludesFilterMaker(self), ExtensionFilterMaker(self), DateFilterMaker(self), SizeFilterMaker(self)]
        for i in self.FilterMakers:
            self.Layout2.addWidget(i)
        self.ChangeType(0)

    def ChangeType(self, index):
        if index == 0:
            self.NotCheckbox.hide()
        for i in range(len(self.FilterMakers)):
            if i == index - 1: 
                self.NotCheckbox.show()
                self.FilterMakers[i].show()
            else: self.FilterMakers[i].hide()
    
    def GetFilter(self) -> Filework.IFileFilter:
        index = self.TypeSelect.currentIndex()
        if index == 0:
            return None
        
        f = self.FilterMakers[index - 1].GetFilter()

        if self.NotCheckbox.isChecked():
            f = Filework.NotFilter(f)
        
        return f


class IFileGrouperMaker(QtWidgets.QWidget):
    def GetGrouper(self) -> Filework.IFileGrouper:
        raise NotImplementedError("Subclasses must implement GetGrouper()")

class NumberGrouperMaker(IFileGrouperMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.NumberEntry = QtWidgets.QLineEdit(self)
        self.NumberEntry.setValidator(QtGui.QIntValidator(0, 1000000, self))
        self.Layout.addWidget(self.NumberEntry)
    
    def GetGrouper(self) -> Filework.IFileGrouper:
        return Filework.NumberGrouper(int(self.NumberEntry.text()))

class ExtensionGrouperMaker(IFileGrouperMaker):
    def __init__(self, parent = None):
        super().__init__(parent)
    
    def GetGrouper(self) -> Filework.IFileGrouper:
        return Filework.ExtensionGrouper()

class DateGrouperMaker(IFileGrouperMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.AccuracySelect = QtWidgets.QComboBox(self)
        self.AccuracySelect.addItems(["по годам", "по месяцам", "по дням"])
        self.Layout.addWidget(self.AccuracySelect)

    def GetGrouper(self) -> Filework.IFileGrouper:
        return Filework.DateGrouper(self.AccuracySelect.currentIndex())

class SizeGrouperMaker(IFileGrouperMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.SizeNumberEntry = QtWidgets.QLineEdit(self)
        self.SizeNumberEntry.setValidator(QtGui.QDoubleValidator(0.0, 1024.0, 3, self))
        self.Layout.addWidget(self.SizeNumberEntry)

        self.SizeMeasureSelect = QtWidgets.QComboBox(self)
        self.SizeMeasureSelect.addItems(["bytes", "KB", "MB", "GB", "TB"])
        self.Layout.addWidget(self.SizeMeasureSelect)
    
    def GetGrouper(self) -> Filework.IFileGrouper:
        return Filework.SizeGrouper(float(self.SizeNumberEntry.text()), self.SizeMeasureSelect.currentText())
            
class AnyGrouperMaker(IFileGrouperMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.TypeSelect = QtWidgets.QComboBox(self)
        self.TypeSelect.addItems(["По номеру", "По расширению", "По дате", "По размеру"])
        self.TypeSelect.currentIndexChanged.connect(self.ChangeType)
        self.Layout.addWidget(self.TypeSelect)

        self.GrouperMakers = [NumberGrouperMaker(self), ExtensionGrouperMaker(self), DateGrouperMaker(self), SizeGrouperMaker(self)]
        for i in self.GrouperMakers:
            self.Layout.addWidget(i)
        self.ChangeType(0)
    
    def ChangeType(self, index):
        for i in range(len(self.GrouperMakers)):
            if i == index: self.GrouperMakers[i].show()
            else: self.GrouperMakers[i].hide()
    
    def GetGrouper(self) -> Filework.IFileGrouper:
        return self.GrouperMakers[self.TypeSelect.currentIndex()].GetGrouper()


class ICommandMaker(QtWidgets.QWidget):
    def GetCommand(self) -> Filework.ICommand:
        raise NotImplementedError("Subclasses must implement GetCommand()")

class SortCommandMaker(ICommandMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QVBoxLayout(self)

        self.Layout1 = QtWidgets.QHBoxLayout()
        self.Layout.addLayout(self.Layout1)

        self.SortByLabel = QtWidgets.QLabel("Сортировать по параметру")
        self.Layout1.addWidget(self.SortByLabel)

        self.SortByEntry = QtWidgets.QLineEdit(self)
        self.Layout1.addWidget(self.SortByEntry)

        self.ReversedCheckbox = QtWidgets.QCheckBox("Обратная сортировка", self)
        self.Layout1.addWidget(self.ReversedCheckbox)

        self.FilterMaker = AnyFilterMaker(self)
        self.Layout.addWidget(self.FilterMaker)

        self.ChildrenCheckbox = QtWidgets.QCheckBox("Повторить в дочерних директориях", self)
        self.Layout1.addWidget(self.ChildrenCheckbox)
    
    def GetCommand(self) -> Filework.ICommand:
        return Filework.SortCommand(self.SortByEntry.text(), self.ReversedCheckbox.isChecked(), self.FilterMaker.GetFilter(), self.ChildrenCheckbox.isChecked())

class RenameCommandMaker(ICommandMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.FormulaEntry = QtWidgets.QLineEdit("<name><ext>", self)
        self.Layout.addWidget(self.FormulaEntry)

        self.ChildrenCheckbox = QtWidgets.QCheckBox("Повторить в дочерних директориях", self)
        self.Layout.addWidget(self.ChildrenCheckbox)
    
    def GetCommand(self) -> Filework.ICommand:
        return Filework.RenameCommand(self.FormulaEntry.text(), self.ChildrenCheckbox.isChecked())

class GroupCommandMaker(ICommandMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QHBoxLayout(self)

        self.GrouperMaker = AnyGrouperMaker(self)
        self.Layout.addWidget(self.GrouperMaker)

        self.ArchiveCheckbox = QtWidgets.QCheckBox("Архивировать", self)
        self.Layout.addWidget(self.ArchiveCheckbox)

        self.ChildrenCheckbox = QtWidgets.QCheckBox("Повторить в дочерних директориях", self)
        self.Layout.addWidget(self.ChildrenCheckbox)
    
    def GetCommand(self) -> Filework.ICommand:
        return Filework.GroupCommand(self.GrouperMaker.GetGrouper(), self.ArchiveCheckbox.isChecked(), self.ChildrenCheckbox.isChecked())

class FlattenCommandMaker(ICommandMaker):
    def __init__(self, parent = None):
        super().__init__(parent)
    
    def GetCommand(self) -> Filework.ICommand:
        return Filework.FlattenCommand()

class AnyCommandMaker(ICommandMaker):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QVBoxLayout(self)

        self.TypeSelect = QtWidgets.QComboBox(self)
        self.TypeSelect.addItems(["Сортировать", "Переименовать", "Сгруппировать", "Сгладить"])
        self.TypeSelect.currentIndexChanged.connect(self.ChangeType)
        self.Layout.addWidget(self.TypeSelect)

        self.CommandMakers = [SortCommandMaker(self), RenameCommandMaker(self), GroupCommandMaker(self), FlattenCommandMaker(self)]
        for i in self.CommandMakers:
            self.Layout.addWidget(i)
        self.ChangeType(0)

    def ChangeType(self, index):
        for i in range(len(self.CommandMakers)):
            if i == index: self.CommandMakers[i].show()
            else: self.CommandMakers[i].hide()
    
    def GetCommand(self) -> Filework.ICommand:
        return self.CommandMakers[self.TypeSelect.currentIndex()].GetCommand()


class CommandsManager(QtWidgets.QWidget):
    def __init__(self, displayHeight: int, parent = None):
        super().__init__(parent)

        self.Layout = QtWidgets.QVBoxLayout(self)

        self.Display = CommandsDisplay(displayHeight, self)
        self.Layout.addWidget(self.Display)

        self.CommandMaker = AnyCommandMaker(self)
        self.Layout.addWidget(self.CommandMaker)

        self.AddButton = QtWidgets.QPushButton("Добавить", self)
        self.AddButton.clicked.connect(self.AddCommand)
        self.Layout.addWidget(self.AddButton)
    
    def AddCommand(self):
        try:
            self.Display.AddCommand(self.CommandMaker.GetCommand())
        except ValueError as e:
            print(e.args[0])
    
    def Execute(self, dirObj: Filework.DirObj):
        self.Display.Execute(dirObj)
        print("Finished")
    
    def GetSerialised(self):
        return self.Display.GetSerialised()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sortinator")
        self.setFixedSize(QtCore.QSize(700, 700))

        self.Central = QtWidgets.QWidget()
        self.setCentralWidget(self.Central)

        self.Layout = QtWidgets.QVBoxLayout(self.Central)
        self.Layout.setGeometry(QtCore.QRect(0, 0, 100, 100))

        self.DirSelect = DirectorySelect(30, 100, self.Central)
        self.Layout.addWidget(self.DirSelect)

        self.Commands = CommandsManager(200, self.Central)
        self.Layout.addWidget(self.Commands)

        self.Layout.addStretch()

        self.Layout1 = QtWidgets.QHBoxLayout()
        self.Layout.addLayout(self.Layout1)

        self.ExecButton = QtWidgets.QPushButton("Исполнить", self)
        self.ExecButton.clicked.connect(self.Execute)
        self.Layout1.addWidget(self.ExecButton)

        self.SaveButton = QtWidgets.QPushButton("Сохранить", self)
        self.SaveButton.clicked.connect(self.Save)
        self.Layout1.addWidget(self.SaveButton)

        self.LoadButton = QtWidgets.QPushButton("Загрузить", self)
        self.LoadButton.clicked.connect(self.Load)
        self.Layout1.addWidget(self.LoadButton)
    
    def Execute(self):
        try:
            dirObj = Filework.DirObj(self.DirSelect.GetPath())
            self.Commands.Execute(dirObj)
        except ValueError as e:
            print(e.args[0])
    
    def Save(self):
        if not Filework.os.path.isdir(SaveDir):
            Filework.os.mkdir(SaveDir)
        
        filePath = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save program",
            SaveDir,
            "JSON Files (*.json);;All Files (*)",
            "JSON Files (*.json)"
        )[0]

        if not filePath.endswith(".json"):
            filePath += ".json"

        pyObj = self.Commands.GetSerialised()

        with open(filePath, 'w') as file:
            json.dump(pyObj, file, indent = 4)
    
    def Load(self):
        filePath = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load program",
            SaveDir,
            "JSON Files (*.json);;All Files (*)",
            "JSON Files (*.json)"
        )[0]

        try:
            with open(filePath, 'r') as file:
                pyObj = json.load(file)

                commandObjs = []
                for i in pyObj:
                    commandObjs.append(Filework.DeserialiseCommand(i))
                
                self.Commands.Display.ClearCommands()
                for i in commandObjs:
                    self.Commands.Display.AddCommand(i)
        except BaseException as e:
            print(e.args[0])



App = QtWidgets.QApplication(sys.argv)
Window = MainWindow()

Window.show()
App.exec()