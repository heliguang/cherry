import logging
import sqlite3
import getpass
import uuid
import glob as gb
import os
import time

from threading import Timer
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QVBoxLayout, QPushButton, \
    QHBoxLayout, QLabel, QLineEdit, QToolButton, QFileDialog

from config import Config
from widget.labelwindow import LabelWindow


class NewProjectWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon(Config.get('application', 'icon')))
        self.setWindowTitle(Config.get('application', 'name') + ' - ' + 'new project')

        projectNameHBoxLayout = QHBoxLayout()
        projectNameHBoxLayout.addWidget(QLabel('project name  '))
        self.projectNameEdit = QLineEdit()
        self.projectNameEdit.returnPressed.connect(self.projectNameEditReturnPressed)
        projectNameHBoxLayout.addWidget(self.projectNameEdit)

        imageLocationHBoxLayout = QHBoxLayout()
        imageLocationHBoxLayout.addWidget(QLabel('image location'))
        self.imageLocationEdit = QLineEdit()
        imageLocationHBoxLayout.addWidget(self.imageLocationEdit)
        self.imageLocationToolButton = QToolButton()
        self.imageLocationToolButton.setIcon(QIcon('./icon/dots-horizontal.png'))
        self.imageLocationToolButton.clicked.connect(self.selectImageLocationClicked)
        imageLocationHBoxLayout.addWidget(self.imageLocationToolButton)

        self.okButton = QPushButton("OK")
        self.okButton.clicked.connect(self.okButtonClicked)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.cancelButtonClicked)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.cancelButton)
        hbox.addWidget(self.okButton)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.statusQLable = QLabel(' ')

        vBoxLayout = QVBoxLayout()
        vBoxLayout.addLayout(projectNameHBoxLayout)
        vBoxLayout.addLayout(imageLocationHBoxLayout)
        vBoxLayout.addWidget(self.statusQLable)
        vBoxLayout.addLayout(vbox)

        self.setLayout(vBoxLayout)

        desktop = QApplication.desktop()
        screenwidth = desktop.width()
        self.resize(screenwidth / 2 * 1.2, screenwidth / 2 * 1.2 * 0.618)
        self.center()

    def setStatusText(self, statsText, delay=2):
        self.statusQLable.setText(statsText)
        tmpClearTime = time.time() + delay - 0.3
        if 'clearStatusTextTime' not in dir():
            self.clearStatusTextTime = tmpClearTime
        elif self.clearStatusTextTime < tmpClearTime:
            self.clearStatusTextTime = tmpClearTime
        elif self.clearStatusTextTime >= tmpClearTime:
            return
        Timer(delay, self.clearStatusText).start()

    def clearStatusText(self):
        if time.time() > self.clearStatusTextTime:
            self.statusQLable.clear()

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Return):
            if self.imageLocationToolButton.hasFocus():
                self.selectImageLocationClicked()
            elif self.okButton.hasFocus():
                self.okButtonClicked()
            elif self.cancelButton.hasFocus():
                self.cancelButtonClicked()

    def projectNameEditReturnPressed(self):
        self.imageLocationEdit.setFocus()

    def selectImageLocationClicked(self):
        imageLocationPath = QFileDialog.getExistingDirectory(self,
                                                              '%s - select image path' % 'cherry', '.',
                                                              QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        self.imageLocationEdit.setText(imageLocationPath)

    def okButtonClicked(self):
        try:
            projectName = self.projectNameEdit.text()
            imageLocationPath = self.imageLocationEdit.text()

            if not projectName or not imageLocationPath:
                self.setStatusText('project name or image location is empty, please input and try again.', delay=2)
                return

            imagePaths = gb.glob(imageLocationPath + os.sep + '*.jpg')
            imagePaths.extend(gb.glob(imageLocationPath + os.sep + '*.jpeg'))
            imagePaths.extend(gb.glob(imageLocationPath + os.sep + '*.png'))

            if len(imagePaths) == 0:
                self.setStatusText('image path does not contains (jpg|jpeg|png), please input and try again.', delay=2)
                return

            #
            self.setStatusText('start create project database', delay=1)
            projectDBName = str(uuid.uuid1()).replace('-', '')

            conn = sqlite3.connect(projectDBName)
            cur = conn.cursor()

            create_table = 'CREATE TABLE IF NOT EXISTS project (name TEXT, remark TEXT, total INTEGER, current INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, author text)'
            cur.execute(create_table)

            cur.execute('INSERT INTO project (name, remark, total, current, author) VALUES (?, ?, ?, ?, ?)',
                        (projectName, imageLocationPath, len(imagePaths), 0, getpass.getuser()))

            create_table = 'CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY, image BLOB, label TEXT, status INTEGER, remark TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, author text)'
            cur.execute(create_table)
            conn.commit()

            for imageCount in range(0, len(imagePaths)):
                with open(imagePaths[imageCount], 'rb') as data:
                    # print(imagePaths[imageCount])
                    self.setStatusText('insert image -> %s / %s' % (imageCount + 1, len(imagePaths)), delay=1)
                    cur.execute('INSERT INTO images (image, status, remark, author) VALUES (?, ?, ?, ?)',
                                (sqlite3.Binary(data.read()), 0, imagePaths[imageCount], getpass.getuser()))

            conn.commit()
            cur.close()
            conn.close()
            self.setStatusText('create project database success', delay=1)

            #
            self.setStatusText('start create project index', delay=1)
            conn = sqlite3.connect("cherry.db")
            cur = conn.cursor()

            create_table = 'CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, db TEXT, remark TEXT, status INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, author text)'
            cur.execute(create_table)

            reset_status = 'UPDATE projects SET status=0'
            cur.execute(reset_status)

            cur.execute('INSERT INTO projects (name, db, status, remark, author) VALUES (?, ?, ?, ?, ?)',
                        (projectName, projectDBName, 1, imageLocationPath, getpass.getuser()))

            conn.commit()
            cur.close()
            conn.close()
            self.setStatusText('create project index success', delay=1)

            self.setStatusText('create project success', delay=3)

            self.close()

            self.labelWindow = LabelWindow()
            self.labelWindow.showMaximized()
        except Exception as e:
            logging.error('创建项目数据失败')

    def cancelButtonClicked(self):
        self.close()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
