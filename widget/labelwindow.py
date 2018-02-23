import sqlite3
import json

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QLineEdit, QMainWindow, QAction, QToolBar

from config import Config
from widget.labelcanvas import LabelCanvas


class LabelWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon(Config.get('application', 'icon')))
        self.setWindowTitle(Config.get('application', 'name') + ' - ' + 'label image')

        labelQLabel = QLabel('')
        labelCoordinates = QLabel('')
        labelEdit = QLineEdit()
        self.statusBar().addPermanentWidget(labelQLabel)
        self.statusBar().addPermanentWidget(labelEdit)
        self.statusBar().addPermanentWidget(labelCoordinates)
        self.statusBar().setStyleSheet("QWidget { background-color: %s }" % '#FEFEFE')

        self.canvas = LabelCanvas(statusbar=self.statusBar(), labelCoordinates=labelCoordinates,
                                  labelQLabel=labelQLabel,
                                  labelEdit=labelEdit)
        self.setCentralWidget(self.canvas)
        self.initToolBar()

        self.db, self.imageNum = self.loadDB()
        self.currentImage = self.loadImage()
        self.canvas.loadPixmap(self.currentImage['pixmap'],
                               labels=json.loads(self.currentImage['label']) if self.currentImage['label'] else None)
        self.setWindowTitle(Config.get('application', 'name') + ' - ' + 'label image - ' +
                            str(self.currentImage['id']) + '/' + str(self.imageNum))
        self.statusBar().showMessage('Ready')

    # 选定选中的数据库与图片数目
    def loadDB(self):
        conn = sqlite3.connect("cherry.db")
        cur = conn.cursor()
        select_db = 'SELECT * FROM projects WHERE status=1'
        cur.execute(select_db)
        conn.commit()
        data = cur.fetchone()
        dbName = data[2]
        cur.close()
        conn.close()

        conn = sqlite3.connect(dbName)
        cur = conn.cursor()
        select_db = 'SELECT * FROM images'
        cur.execute(select_db)
        conn.commit()
        datas = cur.fetchall()
        imageNum = len(datas)
        cur.close()
        conn.close()
        return dbName, imageNum

    # 加载当前标记的图片
    def loadImage(self):
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        select_id = 1
        while True:
            cur.execute('SELECT * FROM images WHERE id=?', (select_id,))
            conn.commit()
            data = cur.fetchone()
            select_id += 1
            if data:
                if not data[2]:
                    cur.close()
                    conn.close()
                    return {'id': int(data[0]), 'pixmap': QPixmap.fromImage(QImage.fromData(data[1])), 'label': data[2]}
            else:
                self.statusBar().showMessage('标记任务全部完成')
                cur.execute('SELECT * FROM images WHERE id=1')
                data = cur.fetchone()
                cur.close()
                conn.close()
                return {'id': int(data[0]), 'pixmap': QPixmap.fromImage(QImage.fromData(data[1])), 'label': data[2]}

    def enlarge(self):
        self.canvas.enlargeByCenter()

    def narrow(self):
        self.canvas.narrowByCenter()

    def restart(self):
        self.canvas.restart()

    def label(self):
        self.canvas.label()

    def undo(self):
        self.canvas.undo()

    # 加载上一张图片
    def last(self):
        self.save()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute('SELECT * FROM images WHERE id=?', (self.currentImage['id'] - 1,))
        conn.commit()
        data = cur.fetchone()
        if data == None:
            self.statusBar().showMessage('当前是第一张图片')
        else:
            self.currentImage = {'id': int(data[0]), 'pixmap': QPixmap.fromImage(QImage.fromData(data[1])), 'label': data[2]}
            self.canvas.loadPixmap(self.currentImage['pixmap'],
                                   labels=json.loads(self.currentImage['label']) if self.currentImage['label'] else None)
            self.setWindowTitle(Config.get('application', 'name') + ' - ' + 'label image - ' +
                                str(self.currentImage['id']) + '/' + str(self.imageNum))
            self.statusBar().showMessage(str(self.currentImage))
        cur.close()
        conn.close()

    # 加载下一张图片
    def next(self):
        self.save()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute('SELECT * FROM images WHERE id=?', (self.currentImage['id'] + 1,))
        conn.commit()
        data = cur.fetchone()
        if data == None:
            self.statusBar().showMessage('当前是最后一张图片')
        else:
            self.currentImage = {'id': int(data[0]), 'pixmap': QPixmap.fromImage(QImage.fromData(data[1])), 'label': data[2]}
            self.canvas.loadPixmap(self.currentImage['pixmap'],
                                   labels=json.loads(self.currentImage['label']) if self.currentImage['label'] else None)
            self.setWindowTitle(Config.get('application', 'name') + ' - ' + 'label image - ' +
                                str(self.currentImage['id']) + '/' + str(self.imageNum))
            self.statusBar().showMessage(str(self.currentImage))
        cur.close()
        conn.close()

    # 将标签信息写入数据库
    def save(self):
        labelstr = json.dumps(self.canvas.save())
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute('UPDATE images SET label=? WHERE id=?', (labelstr, self.currentImage['id']))
        conn.commit()
        cur.close()
        conn.close()

    # 初始化工具栏，并设定快捷键
    def initToolBar(self):
        enlargeAction = QAction(QIcon('icon/enlarge.png'), 'Enlarge', self)
        enlargeAction.setShortcut('Ctrl+E')
        enlargeAction.setStatusTip('Enlarge')
        enlargeAction.triggered.connect(self.enlarge)

        narrowAction = QAction(QIcon('icon/narrow.png'), 'Narrow', self)
        narrowAction.setShortcut('Ctrl+N')
        narrowAction.setStatusTip('Narrow')
        narrowAction.triggered.connect(self.narrow)

        restartAction = QAction(QIcon('icon/redo.png'), 'Restart', self)
        restartAction.setShortcut('Ctrl+R')
        restartAction.setStatusTip('Restart')
        restartAction.triggered.connect(self.restart)

        addLabelAction = QAction(QIcon('icon/add-label.png'), 'Label', self)
        addLabelAction.setShortcut('Ctrl+Q')
        addLabelAction.setStatusTip('Label')
        addLabelAction.triggered.connect(self.label)

        undoAction = QAction(QIcon('icon/undo.png'), 'Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.setStatusTip('Undo')
        undoAction.triggered.connect(self.undo)

        lastImageAction = QAction(QIcon('icon/top.png'), 'Last', self)
        lastImageAction.setStatusTip('Last')
        lastImageAction.triggered.connect(self.last)

        nextImageAction = QAction(QIcon('icon/down.png'), 'Next', self)
        nextImageAction.setStatusTip('Next')
        nextImageAction.triggered.connect(self.next)

        saveAction = QAction(QIcon('icon/save.png'), 'Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save')
        saveAction.triggered.connect(self.save)

        toolbar = QToolBar('Label')
        toolbar.addAction(enlargeAction)
        toolbar.addSeparator()
        toolbar.addAction(narrowAction)
        toolbar.addSeparator()
        toolbar.addAction(restartAction)
        toolbar.addSeparator()
        toolbar.addAction(addLabelAction)
        toolbar.addSeparator()
        toolbar.addAction(undoAction)
        toolbar.addSeparator()
        toolbar.addAction(lastImageAction)
        toolbar.addSeparator()
        toolbar.addAction(nextImageAction)
        toolbar.addSeparator()
        toolbar.addAction(saveAction)
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QWidget { background-color: %s }" % '#FEFEFE')
        self.addToolBar(Qt.RightToolBarArea, toolbar)






