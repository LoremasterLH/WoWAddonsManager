# This Python file uses the following encoding: utf-8
import sys
import os
from collections import defaultdict
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import *
from PySide2.QtCore import *

# Check without emitting event
def checkNoSignal(box, status: bool):
    box.blockSignals(True)
    box.setChecked(status)
    box.blockSignals(False)

class Form(QMainWindow):
#    os.chdir(os.path.dirname(os.path.realpath(__file__)))  # Changes working directory to script's directory
    def __init__(self) -> None:
        # ui setup
        QMainWindow.__init__(self)
        self.setWindowTitle("Addons manager")
        self.setMinimumWidth(270)

        self.settings = QSettings('Addons Manager', 'LoremasterLH')

        self.mainFrame = QFrame(self)
        self.setCentralWidget(self.mainFrame)
        layout = QGridLayout(self.mainFrame)

        # code
        self.root = 'C:/Igre/World of Warcraft/_retail_/WTF/Account/12TUZLA21/'
        self.has_changed = list()
        self.classic: int = -1
        main_character = 'The Maelstrom/Littlehero'

    #        print(self.settings.allKeys())
    #        for key in self.settings.allKeys():
    #            print(key + ':' + str(self.settings.value(key)))

        # Find all the characters
        self.comboBox: QComboBox = QComboBox(self)
        for subdir, dirs, files in os.walk(self.root):
            for file in files:
                if file == 'AddOns.txt':
                    self.comboBox.addItem(subdir[len(self.root):].replace('\\', '/'))
                    self.has_changed.append(False)  # Not yet implemented ... meant for avoiding saving every file when changes are made
        layout.addWidget(self.comboBox, 0, 0)
        self.comboBox.currentIndexChanged.connect(self.changeCharacter)

        self.unique: QCheckBox = QCheckBox(self)
        layout.addWidget(self.unique, 0, 1)
    #        self.unique.stateChanged.connect(self.setUnique)

        self.comboBoxGroups: QComboBox = QComboBox(self)
        self.comboBoxGroups.addItem('Default')  # Add default group
        for key in self.settings.allKeys():  # Add all custom groups
            if self.comboBoxGroups.findText(self.settings.value(key)) == -1:  # Only add new entry if the value doesn't exist yet
                self.comboBoxGroups.addItem(self.settings.value(key))
        self.comboBoxGroups.setEditable(True)
        layout.addWidget(self.comboBoxGroups, 0, 2)
        self.comboBoxGroups.editTextChanged.connect(self.updateGroup)
        self.comboBoxGroups.currentIndexChanged.connect(self.setupData)

        button = QPushButton("(Un)check all")
        button.setCheckable(True)
        layout.addWidget(button, 0, 3)
        button.clicked.connect(self.checkAll)

        button = QPushButton("Save")
        layout.addWidget(button, 0, 4)
        button.clicked.connect(self.saveAllFiles)

        # Scroll area setup
        self.scrollArea = QScrollArea(self)
        layout.addWidget(self.scrollArea, 1, 0, 1, 5)
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
        file = open(self.root + '/' + reference + '/AddOns.txt', 'r')
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
            if prev != text[:4] or prev == 'Rare' and text[:4] == 'Rare' or prev == 'Worl' and text[:4] == 'Worl':
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
#        states = [False] * len(self.addons)
        states = dict()

        # We have to find an AddOns.txt file of this group
        character: str = ''
        for key in self.settings.allKeys():
            if self.settings.value(key) == group_name:
                character = key
                break

        if character == '':
            print('No suitable file found for group ' + group_name)
            return states

        file = open('{0}/{1}/AddOns.txt'.format(self.root, character), 'r')

        # Since not all may exist, initialise the dictionary with all values
        for addon in self.addons:
            states[addon.split(':')[0]] = False

        index: int = 0
        index2: int = 0
        texts = list()
        for line in file:
            text, value = line.split(': ')

            states[text] = True if value == 'enabled\n' else False
#            # Find out which addon we're setting
#            for i in range(len(self.addons)):
#                if text == self.addons[i].split(':')[0]:
#                    states[text] = True if value == 'enabled\n' else False
#                    break

        file.close()
        return states

#        for box in self.findChildren(QGroupBox):
#            print(index)
#            print('{0}: {1}'.format(box.title(), texts[index]))
#            for check in box.findChildren(QCheckBox):
#                print('{0}: {1}'.format(check.text(), texts[index]))
#            index += 1
#            child = self.findChild(QGroupBox, text)  # Check if a QGroupBox exists with the name
#            if child is None:
#                child = self.findChild(QCheckBox, text)  # If no QGroupBox is found, check if a QComboBox exists
#            if child is None:  # If there's no QGroupBox either ... continue
#                continue
#            if value == 'enabled\n':
#                child.setChecked(True);
#            else:
#                child.setChecked(False);

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
        # Reset all checkboxes
#        self.checkAll(False)

        # If we're loading default, we need to read it from a non-unique character (this won't work all that great if manual editing in-game is still done)
#        character: str
#        if self.comboBoxGroups.currentText() == 'Default':
#            # Go through the comboBox until we find a non-unique element
#            for i in range(1, self.comboBox.count()):
#                if not self.settings.contains(self.comboBox.itemText(i)):
#                    character = self.comboBox.itemText(i)
#                    break
#        else:
#        character = self.comboBox.currentText()
#        if self.settings.contains(character):
#            index: int = self.comboBoxGroups.findText(self.settings.value(character))
#            if index == -1:  # Default group
#                self.comboBoxGroups.setCurrentIndex(0)
#            else:
#                self.comboBoxGroups.setCurrentIndex(index)
#        else:  # Default group
#            self.comboBoxGroups.setCurrentIndex(0)

#        file = open('{0}/{1}/AddOns.txt'.format(self.root, character), 'r')
        # Apply group data to the graphic representation
        index: int = 0
        for box in self.findChildren(QGroupBox):
            checkNoSignal(box, self.allGroups[self.comboBoxGroups.currentText()][box.title()])
            index += 1
#            print('{0}: {1}'.format(box.title(), status[index]))
            for check in box.findChildren(QCheckBox):
                checkNoSignal(check, self.allGroups[self.comboBoxGroups.currentText()][check.text()])
#                print('{0}: {1}'.format(check.text(), status[index]))
                index += 1

#        for line in file:
#            text, value = line.split(': ')
#            child = self.findChild(QGroupBox, text)  # Check if a QGroupBox exists with the name
#            if child is None:
#                child = self.findChild(QCheckBox, text)  # If no QGroupBox is found, check if a QComboBox exists
#            if child is None:  # If there's no QGroupBox either ... continue
#                continue
#            if value == 'enabled\n':
#                child.setChecked(True);
#            else:
#                child.setChecked(False);

#        if not self.unique:
#            self.scrollArea.setEnabled(False)

#    def setUnique(self, state: int) -> None:
#        if state:
#            self.settings.setValue(self.comboBox.currentText(), True)
#            self.scrollArea.setEnabled(True)
#        else:
#            self.settings.setValue(self.comboBox.currentText(), False)
#            self.scrollArea.setEnabled(False)

    def checkBoxChanged(self, val: bool) -> None:
        if isinstance(self.sender(), QCheckBox):
            text = self.sender().text()
        else:
            text = self.sender().title()
        self.allGroups[self.comboBoxGroups.currentText()][text] = val

    def updateGroup(self, value: str) -> None:
        self.settings.setValue(self.comboBox.currentText(), value)

    def saveAllFiles(self):
        for i in range(self.comboBox.count()):
            self.saveFile(self.comboBox.itemText(i))


    def saveFile(self, character: str):

        file = open('{0}/{1}/AddOns.txt'.format(self.root, character), 'w')

        # Checkboxes have tripple state ...
        map = dict()
        map[2] = 'enabled\n'
        map[1] = 'enabled\n'
        map[True] = 'enabled\n'
        map[False] = 'disabled\n'
        map[0] = 'disabled\n'

        # Loop through all the boxes and their checkboxes and save the status

        group: str
        if self.settings.contains(character):
            group = self.settings.value(character)
        else:
            group = self.comboBoxGroups.itemText(0)

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
