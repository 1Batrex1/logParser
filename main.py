import configparser
import csv
import logging
import os
import re
import subprocess
from datetime import datetime
from functools import partial
from typing import final

import numpy as np
import screeninfo
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QVBoxLayout, QTextEdit, QPushButton, \
    QGridLayout, QCheckBox, QHBoxLayout, QTableWidget, QTableWidgetItem, QDialog, QLabel

closeAction: final(str) = "Close"
openAction: final(str) = "Open.."
saveAction: final(str) = "Save"
newAction: final(str) = "New"
editAction: final(str) = "Edit"



fileMenuName: final(str) = "File"
configMenuName: final(str) = "Config"
logMenuName: final(str) = "Log"


appName: final(str) = "Log Parser"
configPath: final(str) = "configs"
configExtension: final(str) = ".ini"
dirSeparator: final(str) = "/"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def initFolders():
    cwd = os.getcwd()
    if not os.path.exists(cwd + dirSeparator + configPath):
        os.makedirs(cwd + dirSeparator + configPath)

def loadLogsConfigs():
    configs = os.listdir(configPath)
    configsList = []
    for config in configs:
        configsList.append(os.path.splitext(config)[0])
    return configsList


class MainWindow(QMainWindow):

    class MissingValuesDialog(QDialog):



        def __init__(self, missingValues, parent=None):
            super().__init__(parent)

            windowTitle : final(str) = "Missing levels"
            message : final(str) = "Missing levels in config:"

            self.setWindowTitle(windowTitle)
            layout = QVBoxLayout()

            if missingValues:
                label = QLabel(message)
                layout.addWidget(label)

                for value in missingValues:
                    label = QLabel(str(value))
                    layout.addWidget(label)

            closeButton = QPushButton(closeAction)
            closeButton.clicked.connect(self.close)
            layout.addWidget(closeButton)

            self.setLayout(layout)

    class BadRegexpDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)

            windowTitle : final(str) = "Bad Regexp"
            message : final(str) = "All cell in row must be filed before sorting"

            self.setWindowTitle(windowTitle)
            layout = QVBoxLayout()

            label = QLabel(message)
            layout.addWidget(label)

            closeButton = QPushButton(closeAction)
            closeButton.clicked.connect(self.close)
            layout.addWidget(closeButton)

            self.setLayout(layout)

    class IndexErrorDialog(QDialog):
        def __init__(self, missingValueKey,missingValueIndex, parent=None):
            super().__init__(parent)

            windowTitle : final(str) = "Index Error"
            message : final(str) = "Missing level group in regexp:"

            self.setWindowTitle(windowTitle)
            layout = QVBoxLayout()

            label = QLabel(message)
            layout.addWidget(label)

            label = QLabel(str(missingValueKey) + ":" + str(missingValueIndex))
            layout.addWidget(label)

            closeButton = QPushButton(closeAction)
            closeButton.clicked.connect(self.close)
            layout.addWidget(closeButton)

            self.setLayout(layout)

    class LoadConfigErrorDialog(QDialog):
        def __init__(self, error, parent=None):
            super().__init__(parent)

            windowTitle : final(str) = "Error while loading config"


            self.setWindowTitle(windowTitle)
            layout = QVBoxLayout()

            label = QLabel(str(error))
            layout.addWidget(label)

            close_button = QPushButton(closeAction)
            close_button.clicked.connect(self.close)
            layout.addWidget(close_button)

            self.setLayout(layout)

    class BadDateFormatDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)

            windowTitle : final(str) = "Bad date format"
            message : final(str) = "Invalid date format provided to convert string to data object"

            self.setWindowTitle(windowTitle)
            layout = QVBoxLayout()

            label = QLabel(message)
            layout.addWidget(label)
            closeButton = QPushButton(closeAction)
            closeButton.clicked.connect(self.close)
            layout.addWidget(closeButton)

            self.setLayout(layout)

    class UnableToOpenFileDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)

            windowTitle : final(str) = "Unable to open file"
            message : final(str) = "Unable to open file"

            self.setWindowTitle(windowTitle)
            layout = QVBoxLayout()

            label = QLabel(message)
            layout.addWidget(label)
            closeButton = QPushButton(closeAction)
            closeButton.clicked.connect(self.close)
            layout.addWidget(closeButton)

            self.setLayout(layout)

    def __init__(self):
        super().__init__()

        # Class values

        self.actualConfig = None
        self.chooseMaps = None
        self.timeMap = None
        self.config = None
        self.checkboxLayout = None
        self.regExpFiled = None
        self.columnMap = None
        self.levelPosition = None
        self.logTable = None
        self.logView = None
        self.configLoaded = False
        self.logLevelMap = None
        self.levelCheck = None

        # Init program start

        initFolders()
        self.setWindowTitle(appName)
        self.setScreenSize()
        self.initWindowMenu()
        self.initMainUi()

    def initWindowMenu(self):
        menuBar = self.menuBar()
        self.initFileMenu(menuBar)
        self.initConfigMenu(menuBar)

    def initFileMenu(self, menuBar):
        # Init config file menu layout
        fileMenu = menuBar.addMenu(fileMenuName)

        open = QAction(openAction, self)
        open.triggered.connect(partial(self.openLog))
        fileMenu.addAction(open)

        save = QAction(saveAction, self)
        save.triggered.connect(self.saveAsCsv)
        fileMenu.addAction(save)


    def initConfigMenu(self, menuBar):
        # Init config bar menu layout
        configMenu = menuBar.addMenu(configMenuName)

        edit = QAction(editAction, self)
        edit.triggered.connect(self.editConfig)
        configMenu.addAction(edit)

        logMenu = configMenu.addMenu(configMenuName)
        for config in loadLogsConfigs():
            newConfig = QAction(config, self)
            newConfig.triggered.connect(partial(self.loadConfig, config))
            logMenu.addAction(newConfig)

    def initMainUi(self):



        # Init main window layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)
        top_layout = QGridLayout()

        self.regExpFiled = QTextEdit(self)
        self.regExpFiled.setMaximumSize(int(screeninfo.get_monitors()[0].width * 0.8),
                                        int(screeninfo.get_monitors()[0].height * 0.02))



        regExpButton :final(str) = "Load data to table"
        sortButton :final(str) = "Filter table"

        buttonRegExp = QPushButton(regExpButton, self)
        buttonRegExp.clicked.connect(self.parse_log_data)

        buttonSort = QPushButton(sortButton, self)
        buttonSort.clicked.connect(self.filterTable)

        self.checkboxLayout = QHBoxLayout()
        top_layout.addWidget(self.regExpFiled, 0, 0)
        top_layout.addWidget(buttonSort, 0, 1)
        top_layout.addWidget(buttonRegExp, 0, 2)

        top_layout.addLayout(self.checkboxLayout, 0, 3)
        layout.addLayout(top_layout)

        self.logView = QTextEdit(self)
        self.logView.setReadOnly(True)
        layout.addWidget(self.logView)

        self.logTable = QTableWidget(self)
        self.logTable.setSortingEnabled(True)

        layout.addWidget(self.logTable)

    def loadConfig(self, configName):

        self.clearLayout(self.checkboxLayout)
        logging.debug(f"Starting to load config: {configName}")

        try:
            self.config = configparser.ConfigParser()
            self.actualConfig = configName
            config_file_path = configPath + dirSeparator + configName + configExtension
            logging.debug(f"Reading config file: {config_file_path}")

            # Open config file
            self.config.read(config_file_path)
            logging.debug(f"Config file read successfully: {config_file_path}")

            # Read config values
            self.regExpFiled.setText(self.config.get('regexp', 'regexp'))
            logging.debug(f"Regexp field set: {self.config.get('regexp', 'regexp')}")

            self.logLevelMap = {}
            self.chooseMaps = {}
            for key, value in self.config.items('log_level_map'):
                self.logLevelMap[key] = value.replace("\"", "")
                self.chooseMaps[value.replace("\"", "")] = False
            logging.debug(f"logLevelMap: {self.logLevelMap}")
            logging.debug(f"chooseMaps: {self.chooseMaps}")

            self.timeMap = {}
            for key, value in self.config.items('time_map'):
                self.timeMap[key] = value
            logging.debug(f"timeMap: {self.timeMap}")

            self.configLoaded = True

            self.columnMap = {}
            for index, (key, value) in enumerate(self.config.items('regexp_column_map')):
                if not value.isnumeric():
                    if value.lower() in self.timeMap:
                        value = self.timeMap["log_time_fid"]
                    else:
                        value = self.logLevelMap["log_map_fid"]
                        self.levelPosition = index
                self.columnMap[key] = int(value)
            logging.debug(f"columnMap: {self.columnMap}")

            self.printCheckBoxs()
            logging.debug("Config loaded and UI updated successfully.")
        except configparser.Error as e:
            logging.error(f"ConfigParser error: {e}")
            dialog = self.LoadConfigErrorDialog(e)
            dialog.exec()
            self.resetConfig()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            dialog = self.LoadConfigErrorDialog(e)
            dialog.exec()
            self.resetConfig()


    def resetConfig(self):
        self.clearLayout(self.checkboxLayout)
        self.regExpFiled.setText("")
        self.columnMap = None
        self.timeMap = None
        self.logLevelMap = None
        self.chooseMaps = None
        self.levelPosition = None
        self.actualConfig = None
        self.configLoaded = False



    def editConfig(self):
        if self.actualConfig is None:
            logging.debug("No actual config to edit.")
            return

        configFilePath = configPath + dirSeparator + self.actualConfig + configExtension
        logging.debug(f"Editing config: {configFilePath}")

        try:
            with subprocess.Popen(['cmd', '/c', 'start', '/wait', configFilePath], shell=True) as process:
                process.wait()
            self.loadConfig(self.actualConfig)
        except Exception as error:
            logging.error(f"Error opening file: {error}")
            dialog = self.UnableToOpenFileDialog()
            dialog.exec()


    def printCheckBoxs(self):
        for level in self.logLevelMap.values():

            if level.isnumeric():
                continue
            checkbox = QCheckBox(level, self)
            checkbox.setChecked(False)
            checkbox.clicked.connect(partial(self.changeCheckBoxState, level))
            self.checkboxLayout.addWidget(checkbox)

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

    def openLog(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                  "Log Files (*.log);;Txt Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    self.logView.setText(file.read())
            except:
                dialog = self.UnableToOpenFileDialog()
                dialog.exec()
                return


    def parse_log_data(self):
        # check if you don't load file or configuration
        if not self.configLoaded or self.logView.toPlainText() is None:
            return

        self.logTable.clear()
        self.logTable.setColumnCount(len(self.columnMap))
        self.logTable.setHorizontalHeaderLabels(self.columnMap)
        self.logTable.horizontalHeader().sectionClicked.connect(self.sort_table)
        self.logTable.horizontalHeader().sectionDoubleClicked.connect(self.sort_table_reverse)

        log_lines = self.logView.toPlainText()
        row = 0
        self.levelCheck = set()
        try:
            result = re.findall(self.regExpFiled.toPlainText(), log_lines)
        except:
            return

        for data in result:
            self.logTable.setRowCount(row + 1)

            for colIndex, [logMapKey, logMapIndex] in enumerate(self.columnMap.items()):

                try:
                    cellData = data[logMapIndex - 1]
                except:
                    dialog = self.IndexErrorDialog(logMapKey,logMapIndex)
                    dialog.exec()
                    return

                if logMapIndex == int(self.timeMap["log_time_fid"]):
                    try:
                        cellData = self.praiseDate(cellData)
                    except Exception:
                        dialog = self.BadDateFormatDialog()
                        dialog.exec()
                        return

                if logMapIndex == int(self.logLevelMap["log_map_fid"]):
                    if cellData not in self.levelCheck:
                        self.levelCheck.add(cellData)

                item = QTableWidgetItem(cellData)
                self.logTable.setItem(row, colIndex, item)

            row += 1

        self.logTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.logTable.resizeColumnsToContents()

        self.logTable.resizeRowsToContents()

    def filterTable(self):

        if self.logLevelMap is None or self.logTable.rowCount() == 0 or self.levelCheck is None:
            return

        for x in range(len(self.columnMap)):
            if self.logTable.item(0, x) is None:
                dialog = self.BadRegexpDialog()
                dialog.exec()
                return

        # Check configuration level
        missing_values = [value for value in self.levelCheck if value not in self.logLevelMap.values()]
        if missing_values:
            dialog = self.MissingValuesDialog(missing_values, self)
            dialog.exec()
            return

        # Get all levels from table to vector
        column_data = np.array(
            [self.logTable.item(row_index, self.levelPosition).text() for row_index in
             range(self.logTable.rowCount())])

        # Find rows to show
        should_show_rows = np.vectorize(lambda x: self.chooseMaps[x])(column_data)

        # Update row configuration depends on user choice
        for row_index, should_show in enumerate(should_show_rows):
            self.logTable.setRowHidden(row_index, not should_show)

        # Update table view
        self.logTable.viewport().update()

    def sort_table(self, column):
        self.logTable.sortItems(column)

    def sort_table_reverse(self, column):
        self.logTable.sortItems(column, Qt.SortOrder.DescendingOrder)

    def setScreenSize(self):
        width = screeninfo.get_monitors()[0].width
        height = screeninfo.get_monitors()[0].height
        self.setGeometry(width // 8, height // 8, int(width * 0.8), int(height * 0.8))

    def changeCheckBoxState(self, level):
        if self.chooseMaps[level]:
            self.chooseMaps[level] = False
            return
        self.chooseMaps[level] = True

    def praiseDate(self, cellData):
        try:
            date = datetime.strptime(cellData, self.timeMap["time_format"])
            return date.strftime(self.timeMap["req_format"])
        except:
            raise Exception

    def saveAsCsv(self):

        if self.logTable.rowCount() == 0 or self.chooseMaps == {}:
            return
        visible_rows_data = []
        for row_index in range(self.logTable.rowCount()):
            if not self.logTable.isRowHidden(row_index):
                row_data = [self.logTable.item(row_index, col).text().strip().replace("\r\n", "\n") for col in
                            range(self.logTable.columnCount())]
                visible_rows_data.append(row_data)

        file_path, _ = QFileDialog.getSaveFileName(None, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=';')
                    csvwriter.writerow([self.logTable.horizontalHeaderItem(col).text() for col in
                                        range(self.logTable.columnCount())])
                    csvwriter.writerows(visible_rows_data)
            except:
                dialog = self.UnableToOpenFileDialog()
                dialog.exec()
                return



def startapp():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


startapp()
