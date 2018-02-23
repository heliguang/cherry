import logging
import sqlite3

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from config import Config
from widget.newprojectwindow import NewProjectWindow
from widget.labelwindow import LabelWindow


class WelcomeWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(Config.get('application', 'icon')))
        self.setWindowTitle(Config.get('application', 'name'))

        hbox = QHBoxLayout()

        # 窗口左侧项目列表区域
        self.projectListWidget = QListWidget()
        self.projectListWidget.itemDoubleClicked.connect(self.projectListItemDoubleClick)
        try:
            conn = sqlite3.connect("cherry.db")
            cur = conn.cursor()
            projectItemCount = 0
            for row in cur.execute('SELECT * FROM projects'):
                projectItemCount += 1
                projectListItemWidget = QListWidgetItem()
                projectListItemWidget.setSizeHint(QSize(90, 60))
                self.projectListWidget.addItem(projectListItemWidget)
                if projectItemCount > 9:
                    labelImageName = 'icon/dot1.png'
                else:
                    labelImageName = 'icon/s-number-%s.png' % str(projectItemCount)
                label = ProjectItemLabel(row[1], row[2], labelImageName)
                self.projectListWidget.setItemWidget(projectListItemWidget, label)

            if self.projectListWidget.count() > 0:
                for row in cur.execute('SELECT * FROM projects WHERE status=1'):
                    self.projectListWidget.setCurrentRow(row[0] - 1)
                hbox.addWidget(self.projectListWidget, stretch=2)
        except Exception:
            logging.error('项目数据库读取与初始化界面失败')

        # 右侧布局
        vbox = QVBoxLayout()

        iconhbox = QHBoxLayout()
        lbl = QLabel(self)
        lbl.setPixmap(QPixmap(Config.get('application', 'icon')))
        iconhbox.addWidget(QLabel(), stretch=1)
        iconhbox.addWidget(lbl, stretch=1)
        iconhbox.addWidget(QLabel(), stretch=1)

        # 新建项目按钮
        self.newProjectButton = QPushButton()
        self.newProjectButton.setText("新建项目")
        self.newProjectButton.clicked.connect(self.newProjectButtonClick)

        vbox.addWidget(QLabel(), stretch=1)
        vbox.addLayout(iconhbox, stretch=1)
        vbox.addWidget(QLabel(), stretch=2)
        vbox.addWidget(self.newProjectButton, stretch=1)

        hbox.addLayout(vbox, stretch=3)
        self.setLayout(hbox)

        # 设置窗口大小与位置
        desktop = QApplication.desktop()
        screenwidth = desktop.width()
        self.resize(screenwidth / 2, screenwidth / 2 * 0.618)
        self.center()

    # 窗口可见时，监听回车键
    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Return):
            if self.projectListWidget.hasFocus():
                self.projectListItemDoubleClick()
            elif self.newProjectButton.hasFocus():
                self.newProjectButtonClick()

    # 打开新建项目界面
    def newProjectButtonClick(self):
        self.close()

        self.newProjectWindow = NewProjectWindow()
        self.newProjectWindow.show()

    # 项目名被双击时，回调
    def projectListItemDoubleClick(self):
        widget = self.projectListWidget.itemWidget(self.projectListWidget.currentItem())
        conn = sqlite3.connect("cherry.db")
        cur = conn.cursor()

        reset_status = 'UPDATE projects SET status=0 WHERE status=1'
        cur.execute(reset_status)

        set_status = r"UPDATE projects SET status=? WHERE db=?"
        cur.execute(set_status, (1, widget.get_lb_subtitle()))

        conn.commit()
        cur.close()
        conn.close()

        self.close()

        # 打开标记窗口
        self.labelWindow = LabelWindow()
        self.labelWindow.showMaximized()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class ProjectItemLabel(QWidget):
    def __init__(self, title, subtitle, icon_path):
        super(ProjectItemLabel, self).__init__()
        self.lb_title = QLabel(title)
        self.lb_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.lb_subtitle = QLabel(subtitle)
        self.lb_subtitle.setFont(QFont("Arial", 8, QFont.StyleItalic))
        self.lb_icon = QLabel()
        self.lb_icon.setFixedSize(40, 40)
        pixMap = QPixmap(icon_path).scaled(self.lb_icon.width(), self.lb_icon.height())
        self.lb_icon.setPixmap(pixMap)
        self.lb_icon.setStyleSheet("QWidget { background-color: %s }" % '#EE2C2C')
        self.init_ui()

    def init_ui(self):
        ly_main = QHBoxLayout()
        ly_right = QVBoxLayout()
        ly_right.addWidget(self.lb_title)
        ly_right.addWidget(self.lb_subtitle)
        ly_right.setAlignment(Qt.AlignVCenter)
        ly_main.addWidget(self.lb_icon)
        ly_main.addLayout(ly_right)
        self.setLayout(ly_main)
        self.resize(90, 60)

    def get_lb_title(self):
        return self.lb_title.text()

    def get_lb_subtitle(self):
        return self.lb_subtitle.text()