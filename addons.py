# This Python file uses the following encoding: utf-8
import sys
import os
from collections import defaultdict
from shutil import copyfile
from filecmp import cmp
from PySide2.QtWidgets import QGroupBox, QMainWindow, QFrame, QGridLayout, QComboBox, QPushButton, QScrollArea, QWidget, QVBoxLayout, QCheckBox, QApplication
from PySide2.QtCore import QSettings

# Check without emitting event
def checkNoSignal(box, status: bool):
    box.blockSignals(True)
    box.setChecked(status)
    box.blockSignals(False)

class Form(QMainWindow):
    os.chdir(os.path.dirname(os.path.realpath(__file__)))  # Changes working directory to script's directory

    def __init__(self) -> None:
        # ui setup
        QMainWindow.__init__(self)
        self.setWindowTitle("Addons manager")
        self.setMinimumWidth(270)

        self.settings = QSettings('Addons Manager', 'LoremasterLH')

        self.mainFrame = QFrame(self)
        self.setCentralWidget(self.mainFrame)
        layout = QGridLayout(self.mainFrame)

        # setup
        self.root = 'C:/Igre/World of Warcraft/_retail_/WTF/Account/12TUZLA21/'
        self.groups_dir = 'groups/'
        if not os.path.exists(self.groups_dir):
            os.makedirs(self.groups_dir)
        self.has_changed = list()
        self.classic: int = -1
        main_character = 'The Maelstrom/Littlehero'

        # Find all the characters
        self.comboBox: QComboBox = QComboBox(self)
        for subdir, dirs, files in os.walk(self.root):
            for file in files:
                if file == 'AddOns.txt':
                    self.comboBox.addItem(subdir[len(self.root):].replace('\\', '/'))
                    self.has_changed.append(False)  # Not yet implemented ... meant for avoiding saving every file when changes are made
        layout.addWidget(self.comboBox, 0, 0)
        self.comboBox.currentIndexChanged.connect(self.changeCharacter)

        self.comboBoxGroups: QComboBox = QComboBox(self)
        self.comboBoxGroups.addItem('Default')  # Add default group
        for key in self.settings.allKeys():  # Add all custom groups
            if self.comboBoxGroups.findText(self.settings.value(key)) == -1:  # Only add new entry if the value doesn't exist yet
                self.comboBoxGroups.addItem(self.settings.value(key))
        self.comboBoxGroups.setEditable(True)
        layout.addWidget(self.comboBoxGroups, 0, 1)
        self.comboBoxGroups.editTextChanged.connect(self.updateGroup)
        self.comboBoxGroups.currentIndexChanged.connect(self.setupData)

        self.buttonConfirm = QPushButton("Confirm")
        layout.addWidget(self.buttonConfirm, 1, 1)
        self.buttonConfirm.hide()
        self.buttonConfirm.clicked.connect(self.confirmGroup)

        button = QPushButton("(Un)check all")
        button.setCheckable(True)
        layout.addWidget(button, 0, 2)
        button.clicked.connect(self.checkAll)

        button = QPushButton("Save")
        layout.addWidget(button, 0, 3)
        button.clicked.connect(self.saveAllFiles)

        # Scroll area setup
        self.scrollArea = QScrollArea(self)
        layout.addWidget(self.scrollArea, 2, 0, 1, 4)
        self.scrollArea.setWidgetResizable(True)

        scrollAreaContents = QWidget()
        self.scrollArea.setWidget(scrollAreaContents)
        self.innerLayout = QVBoxLayout(scrollAreaContents)

        # Load ui components
        self.loadData(main_character)
        # Load all groups from files. Nothing else will be read.
        self.allGroups = defaultdict(lambda: False)
        for i in range(self.comboBoxGroups.count()):
            self.allGroups[self.comboBoxGroups.itemText(i)] = self.getGroupData(self.comboBoxGroups.itemText(i))

        # load data for first character
        self.setupData()


    # Construct the groupboxes based on reference character; any addons not in it's AddOns.txt will be ignored. Only better way would be parsing the addons folder, but that is rather complex ... not to mention modules
    def loadData(self, reference: str) -> None:
        # Open reference file to see which addons we have
        file = open('{0}{1}/AddOns.txt'.format(self.root, reference), 'r')
        text = ''

        # Sort the addons for proper grouping
        self.addons = list()
        for line in file:
            self.addons.append(line)
        file.close()
        self.addons.sort(key=lambda x: x.replace('-', '_'))  # As '-' is considered before ' ', we have to take care of it for proper order

        for i in range(len(self.addons)):
            prev = text[:4]  # Save previous value to determine if it's the same group
            text, value = self.addons[i].split(': ')

            # Different addons with similar names have to be separated; another way would be to pick the first one alphabetically
            if prev != text[:4] or prev == 'Rare' and text[:4] == 'Rare' or prev == 'Worl' and text[:4] == 'Worl' or prev == 'Tran' and text[:4] == 'Tran':
                groupBox: QGroupBox = QGroupBox(text)
                groupBox.setObjectName(text)
                groupBox.setLayout(QVBoxLayout())
                groupBox.setCheckable(True)
                self.innerLayout.addWidget(groupBox)
                groupBox.setChecked(False)
                groupBox.toggled.connect(self.checkBoxChanged)

            else:
#                Remove classic ... revisit as well as others that I always want disabled
#                if text.find('classic') != -1 and self.classic == -1:
#                    self.classic = i
#                    self.addons[i] = text + ': disabled\n'
#                    continue

                box: QCheckBox = QCheckBox(text)
                box.setObjectName(text)
                groupBox.layout().addWidget(box)
                box.setChecked(False)
                box.stateChanged.connect(self.checkBoxChanged)

    # Convenience method for enabling/disabling all checkboxes
    def checkAll(self, status: bool) -> None:
        children = self.findChildren(QGroupBox)
        for box in children:
            for check in box.findChildren(QCheckBox):
                check.setChecked(status)
            box.setChecked(status)
    # Returns a list of bool values representing state of the group
    def getGroupData(self, group_name: str) -> dict():
        states = dict()

        # We have to find an AddOns.txt file of this group
        if not os.path.isfile('{0}{1}.txt'.format(self.groups_dir, group_name)):
            character: str = ''
            for key in self.settings.allKeys():
                if self.settings.value(key) == group_name:
                    character = key
                    break
            if character == '':
                print('No suitable file found for group ' + group_name)
                return states
            copyfile('{0}{1}/AddOns.txt'.format(self.root, character), '{0}{1}.txt'.format(self.groups_dir, group_name))

        # Since it's possible not exist, initialise the dictionary with all values
        for addon in self.addons:
            states[addon.split(':')[0]] = False

        file = open('{0}{1}.txt'.format(self.groups_dir, group_name))
        for line in file:
            text, value = line.split(': ')
            states[text] = True if value == 'enabled\n' else False
        file.close()

        return states

    # Slot used to confirm the newly entered group and avoid creating a new group for every keypress
    def confirmGroup(self) -> None:
        self.settings.setValue(self.comboBox.currentText(), self.comboBoxGroups.currentText())
        self.allGroups[self.comboBoxGroups.currentText()] = self.getGroupData(self.comboBoxGroups.currentText())
        self.saveFile(self.comboBoxGroups.currentText())
        self.buttonConfirm.hide()

    # Triggers when text is entered into the comboBox
    def updateGroup(self, value: str) -> None:
        if self.comboBoxGroups.currentText() in self.allGroups:
            self.buttonConfirm.hide()
        else:
            self.buttonConfirm.show()

    # Change the groups dropdown to the proper group when changing character
    def changeCharacter(self) -> None:
        if self.settings.contains(self.comboBox.currentText()):
            index: int = self.comboBoxGroups.findText(self.settings.value(self.comboBox.currentText()))
            if index != -1:
                self.comboBoxGroups.setCurrentIndex(index)
            else:
                print('Character has undefined group ' + self.settings.value(self.comboBox.currentText()))
        else:
            self.comboBoxGroups.setCurrentIndex(0)
        self.setupData()

    # Load the data for the character
    def setupData(self) -> None:
        self.settings.setValue(self.comboBox.currentText(), self.comboBoxGroups.currentText())
        for box in self.findChildren(QGroupBox):
            checkNoSignal(box, self.allGroups[self.comboBoxGroups.currentText()][box.title()])
            for check in box.findChildren(QCheckBox):
                checkNoSignal(check, self.allGroups[self.comboBoxGroups.currentText()][check.text()])

    def checkBoxChanged(self, val: bool) -> None:
        if isinstance(self.sender(), QCheckBox):
            self.allGroups[self.comboBoxGroups.currentText()][self.sender().text()] = val
        else:
            self.allGroups[self.comboBoxGroups.currentText()][self.sender().title()] = val

    def saveAllFiles(self) -> None:
        # Save group files
        for i in range(self.comboBoxGroups.count()):
            self.saveFile(self.comboBoxGroups.itemText(i))
        # Copy group files to appropriate characters
        for i in range(self.comboBox.count()):
            char_file = '{0}{1}/AddOns.txt'.format(self.root, self.comboBox.itemText(i))
            group_file = '{0}{1}.txt'.format(self.groups_dir, self.settings.value(self.comboBox.itemText(i))) if self.settings.contains(self.comboBox.itemText(i)) else '{0}{1}.txt'.format(self.groups_dir, self.comboBoxGroups.itemText(0))
            # Only overwrite if files are different
            if not cmp(group_file, char_file):
                copyfile(group_file, char_file)


    def saveFile(self, group: str) -> None:
        # Checkboxes have triple state ...
        map = dict()
        map[True] = map[2] = map[1] = 'enabled\n'
        map[False] = map[0] = 'disabled\n'

        file = open('{0}{1}.txt'.format(self.groups_dir, group), 'w')
        for box in self.findChildren(QGroupBox):
            file.write('{0}: {1}'.format(box.title(), map[self.allGroups[group][box.title()]]))
            for check in box.findChildren(QCheckBox):
                file.write('{0}: {1}'.format(check.text(), map[self.allGroups[group][check.text()]]))
        file.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()
