import math

from PyQt5.QtCore import QRect, QPoint, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QFont
from PyQt5.QtWidgets import QWidget


class LabelCanvas(QWidget):

    def __init__(self, statusbar=None, labelCoordinates=None, labelQLabel=None, labelEdit=None):
        super(LabelCanvas, self).__init__()
        self.statusbar = statusbar
        self.labelCoordinates = labelCoordinates
        self.labelEdit = labelEdit
        self.labelQLabel = labelQLabel
        if self.labelQLabel:
            self.labelQLabel.hide()
        if self.labelEdit:
            self.labelEdit.hide()
            self.labelEdit.returnPressed.connect(self.labelEditEnterPress)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

        self.painter = QPainter()
        self.scaleRate = 0.2

        self.pixmap = QPixmap('icon/sample.jpg')
        self.pmapRect = self.pixmap.rect()
        self.pmapShowAreaRect = self.pixmap.rect()
        self.drag = False
        self.labels = ()

        self.mousex = 0
        self.mousey = 0
        self.labels = []
        self.templabel = []
        self.labeling = False
        self.labelsRect = []
        self.deleteRects = []
        self.textRects = []

    def loadPixmap(self, pixmap, labels=None):
        self.pixmap = pixmap
        self.pmapRect = pixmap.rect()
        self.pmapShowAreaRect = pixmap.rect()
        self.labels.clear()
        if labels:
            self.labels.extend(labels)
        self.repaint()

    def paintEvent(self, e):
        self.painter.begin(self)

        # 绘制图片内容
        self.painter.drawPixmap(self.rect(), self.pixmap, self.pmapShowAreaRect)

        # 绘制图片区域预览
        self.painter.setPen(QColor(0, 0, 0))
        scale = min(self.width() / self.pixmap.width() / 5, self.height() / self.pixmap.height() / 5)
        self.pmapPreRect = QRect(0, 0, self.pixmap.width() * scale, self.pixmap.height() * scale)
        margin = int(min(self.width(), self.height()) / 16)
        self.pmapPreRect.moveTopRight(QPoint(self.width() - margin, margin))
        self.painter.drawRect(self.pmapPreRect)

        # 绘制图片展示区域预览
        self.painter.setPen(QColor(255, 0, 0))
        pmapprerect = self.pmapPreRect.getRect()
        pmapshowarearect = self.pmapShowAreaRect.getRect()
        x = pmapprerect[0] + self.pmapPreRect.width() * pmapshowarearect[0] / self.pixmap.width()
        y = pmapprerect[1] + self.pmapPreRect.height() * pmapshowarearect[1] / self.pixmap.height()
        w = scale * self.pmapShowAreaRect.width()
        h = scale * self.pmapShowAreaRect.height()
        self.pmapShowAreaPreRect = QRect(x, y, w, h)
        self.painter.drawRect(self.pmapShowAreaPreRect)

        self.dragAreaRect = QRect(self.pmapPreRect.x() - self.pmapShowAreaPreRect.width(),
                                  self.pmapPreRect.y() - self.pmapShowAreaPreRect.height(),
                                  self.pmapShowAreaPreRect.width() + self.pmapPreRect.width(),
                                  self.pmapShowAreaPreRect.height() + self.pmapPreRect.height())

        # 绘制缩放中心点标线
        self.painter.setPen(QColor(255, 0, 0))
        self.painter.drawLine(self.width() / 3, self.height() / 2, self.width() / 3 * 2, self.height() / 2)
        self.painter.drawLine(self.width() / 2, self.height() / 3, self.width() / 2, self.height() / 3 * 2)

        # 绘制鼠标位置标线
        if self.labeling:
            self.painter.setPen(QColor(0, 0, 0))
            self.painter.drawLine(self.mousex, 0, self.mousex, self.height())
            self.painter.drawLine(0, self.mousey, self.width(), self.mousey)

        # 绘制正在编辑中的label位置
        if self.templabel:
            for i in range(int(len(self.templabel) / 2)):
                imagex, imagey = self.templabel[0 + 2 * i], self.templabel[1 + 2 * i]
                if self.pmapShowAreaRect.contains(imagex, imagey):
                    widgetx, widgety = self.imageXY2WidgetXY(imagex, imagey)
                    self.painter.setPen(QPen(Qt.red, 5))
                    self.painter.drawPoint(widgetx, widgety)

                    pen = QPen(Qt.black, 2, Qt.SolidLine)
                    pen.setStyle(Qt.DashDotDotLine)
                    self.painter.setPen(pen)
                    self.painter.drawLine(widgetx, 0, widgetx, self.height())
                    self.painter.drawLine(0, widgety, self.width(), widgety)

        # 绘制已标记内容
        self.deleteRects.clear()
        self.textRects.clear()

        self.painter.setPen(QColor(168, 34, 3))
        self.painter.setFont(QFont('Decorative', 12))
        metrics = self.painter.fontMetrics()
        deleteRectWidth, deleteRectHeight = metrics.height() * 1.2, metrics.height() * 1.2

        separatorheight = margin / 10

        pmapprerect = self.pmapPreRect.getRect()
        topRightx, topRighty = self.width() - margin, pmapprerect[1] + pmapprerect[3] + margin / 4
        for i in range(len(self.labels)):
            label = self.labels[i]
            # 绘制文字展示信息
            text = label[4]
            deleteRect = QRect(topRightx - deleteRectWidth, topRighty + (deleteRectHeight + separatorheight) * i,
                               deleteRectWidth, deleteRectHeight)
            self.painter.drawRect(deleteRect)
            self.painter.drawLine(deleteRect.topLeft(), deleteRect.bottomRight())
            self.painter.drawLine(deleteRect.topRight(), deleteRect.bottomLeft())
            self.deleteRects.append(deleteRect)

            deleterect = deleteRect.getRect()
            textWidth, textHeight = metrics.width(text), metrics.height()
            textRect = QRect(deleterect[0] - textWidth - metrics.height(), deleterect[1], textWidth + metrics.height(), deleterect[3])
            self.painter.drawRect(textRect)
            self.painter.drawText(textRect, Qt.AlignCenter, text)
            self.textRects.append(textRect)
            # 在图片上绘制标签矩形框
            labelPixmapX, labelPixmapY, labelPixmapWidth,  labelPixmapHeight = label[:4]
            labelPixmapRect = QRect(labelPixmapX, labelPixmapY, labelPixmapWidth,  labelPixmapHeight)
            intersectedRect = self.pmapShowAreaRect.intersected(labelPixmapRect)
            if intersectedRect:
                pixmapTopLeftPoint, pixmapBottomRightPoint = intersectedRect.topLeft(), intersectedRect.bottomRight()
                widgetTopLeftPointX, widgetTopLeftPointY = self.imageXY2WidgetXY(pixmapTopLeftPoint.x(), pixmapTopLeftPoint.y())
                widgetTopLeftPoint = QPoint(widgetTopLeftPointX, widgetTopLeftPointY)
                widgetBottomRightPointX, widgetBottomRightPointY = self.imageXY2WidgetXY(pixmapBottomRightPoint.x(), pixmapBottomRightPoint.y())
                widgetBottomRightPoint = QPoint(widgetBottomRightPointX, widgetBottomRightPointY)
                labelRect = QRect(widgetTopLeftPoint, widgetBottomRightPoint)
                self.painter.drawRect(labelRect)
                # 绘制标签名
                labelrect = labelRect.getRect()
                textRect1 = QRect(labelrect[0], labelrect[1] - textHeight, textWidth, textHeight)
                # self.painter.drawRect(textRect1)
                self.painter.drawText(textRect1, Qt.AlignCenter, text)

        self.painter.end()

    # 将图片中像素坐标转化为控件坐标
    def imageXY2WidgetXY(self, imagex, imagey):
        pmapshowarearect = self.pmapShowAreaRect.getRect()
        widgetx = (imagex - pmapshowarearect[0]) / pmapshowarearect[2] * self.width()
        widgety = (imagey - pmapshowarearect[1]) / pmapshowarearect[3] * self.height()
        return widgetx, widgety

    # 恢复图片初加载状态
    def restart(self):
        self.pmapRect = self.pixmap.rect()
        self.pmapShowAreaRect = self.pixmap.rect()
        self.repaint()

    # 初始化一个新的标签
    def label(self):
        self.templabel.clear()
        self.labeling = True
        if self.labelQLabel:
            self.labelQLabel.setText('')
            self.labelQLabel.show()
        self.status('开始创建标签', delay=500)
        self.repaint()

    # 移除最后一次添加的像素点
    def undo(self):
        self.removeTempPoint()

    # 返回标签内容
    def save(self):
        self.clearStatus()
        return self.labels

    def clearStatus(self):
        if self.labelQLabel:
            self.labelQLabel.hide()
        if self.labelEdit:
            self.labelEdit.hide()
        if self.templabel:
            self.templabel.clear()
        self.labeling = False
        self.repaint()

    # 添加标记点
    def addTempPoint(self, x, y):
        if self.labelQLabel.isHidden():
            self.labelQLabel.show()

        self.templabel.append(x)
        self.templabel.append(y)

        self.statusLabel('创建标签->' + str(self.templabel))

        if len(self.templabel) == 4:
            self.statusLabel('标签内容为->' + str(self.templabel) + ' 请输入标签名->')
            self.labeling = False
            self.labelEdit.setText('')
            self.labelEdit.setFocus()
            self.labelEdit.show()
            self.repaint()

    # 移除标记点
    def removeTempPoint(self):
        if self.templabel:
            self.templabel = self.templabel[:-2]
            self.repaint()

            self.labelEdit.setText('')
            self.labelEdit.hide()
            self.labelQLabel.setText('标签内容->' + str(self.templabel))
            if len(self.templabel) == 0:
                self.labelQLabel.hide()

    # 监听滚轮事件
    def wheelEvent(self, event):
        if event.angleDelta:
            if event.angleDelta().y() / 120 >= 1:
                self.enlargeByCenter()
            else:
                self.narrowByCenter()

    # 监听鼠标双击事件
    def mouseDoubleClickEvent(self, event):
        if self.labeling:
            if len(self.templabel) >= 4:
                self.label()
                self.status('标记错误，已重置', delay=800)
                return

            pointx = math.ceil(
                self.pmapShowAreaRect.getRect()[0] + (self.pmapShowAreaRect.width() * event.pos().x() / self.width()))
            pointy = math.ceil(
                self.pmapShowAreaRect.getRect()[1] + (self.pmapShowAreaRect.height() * event.pos().y() / self.height()))
            if self.pmapRect.contains(pointx, pointy):
                self.addTempPoint(pointx, pointy)
            else:
                self.status('请选择图片区域', delay=500)

    # 监听键盘ESC键按下
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.labelQLabel:
                self.labelQLabel.hide()
            if self.labelEdit:
                self.labelEdit.hide()
            if self.templabel:
                self.templabel.clear()
            self.labeling = False
            self.repaint()

    def labelEditEnterPress(self):
        self.labelEdit.hide()
        if self.labelQLabel:
            self.labelQLabel.hide()

        labelText = self.labelEdit.text()
        templabelrect = [min(self.templabel[0], self.templabel[2]), min(self.templabel[1], self.templabel[3]),
                         abs(self.templabel[0] - self.templabel[2]), abs(self.templabel[1] - self.templabel[3]),
                         '默认标签名' if labelText.strip() == '' else labelText.strip()]
        self.status('标签创建成功->' + str(templabelrect), delay=1000)
        self.labels.append(templabelrect)
        self.templabel.clear()
        self.labeling = False
        self.repaint()

    # 监听鼠标按下事件
    def mousePressEvent(self, event):
        if self.pmapShowAreaPreRect.contains(event.pos().x(), event.pos().y()):
            self.drag = True
        elif self.pmapPreRect.contains(event.pos().x(), event.pos().y()):
            pmapprerect = self.pmapPreRect.getRect()
            pmaprect = self.pmapRect.getRect()
            scale = pmaprect[2] / pmapprerect[2]
            ximage = (event.pos().x() - pmapprerect[0]) * scale
            yimage = (event.pos().y() - pmapprerect[1]) * scale
            self.pmapShowAreaRect.moveCenter(QPoint(ximage, yimage))
            self.repaint()
        else:
            self.labelTextClickCheck(event.pos().x(), event.pos().y())

    # 鼠标点击到标签逻辑
    def labelTextClickCheck(self, widgetx, widgety):
        for i in range(len(self.textRects)):
            if self.textRects[i].contains(widgetx, widgety):
                self.status(str(self.labels[i]), delay=1000)
                labelx, labely, labelwidth, labelheight = self.labels[i][:4]
                self.pmapShowAreaRect.moveCenter(QRect(labelx, labely, labelwidth, labelheight).center())
                self.repaint()
                return

        for i in range(len(self.deleteRects)):
            if self.deleteRects[i].contains(widgetx, widgety):
                self.labels.pop(i)
                self.repaint()
                return

    # 鼠标移动事件
    def mouseMoveEvent(self, event):
        pointx = math.ceil(self.pmapShowAreaRect.getRect()[0] + (self.pmapShowAreaRect.width() * event.pos().x() / self.width()))
        pointy = math.ceil(self.pmapShowAreaRect.getRect()[1] + (self.pmapShowAreaRect.height() * event.pos().y() / self.height()))
        self.labelCoordinates.setText('X: %s Y: %s' % (pointx, pointy))

        if self.drag and self.dragAreaRect.contains(event.pos().x(), event.pos().y()):
            pmapprerect = self.pmapPreRect.getRect()
            pmaprect = self.pmapRect.getRect()
            scale = pmaprect[2] / pmapprerect[2]
            ximage = (event.pos().x() - pmapprerect[0]) * scale
            yimage = (event.pos().y() - pmapprerect[1]) * scale
            self.pmapShowAreaRect.moveCenter(QPoint(ximage, yimage))
            self.repaint()
        else:
            if self.pmapPreRect.contains(event.pos().x(), event.pos().y()):
                self.mousex, self.mousey = 0, 0
                self.repaint()
            else:
                self.mousex, self.mousey = event.pos().x(), event.pos().y()
                self.repaint()

    def mouseReleaseEvent(self, event):
        self.drag = False

    # 以图片中心放大图片
    def enlargeByCenter(self):
        pmapshowarearect = self.pmapShowAreaRect.getRect()
        pmaprect = self.pmapRect.getRect()
        if pmapshowarearect[2] <= pmaprect[2] / 20 or pmapshowarearect[3] <= pmaprect[3] / 20:
            return

        self.pmapShowAreaRect.adjust(self.pmapShowAreaRect.width() * self.scaleRate, self.pmapShowAreaRect.height() * self.scaleRate,
                           -self.pmapShowAreaRect.width() * self.scaleRate, -self.pmapShowAreaRect.height() * self.scaleRate)
        self.repaint()

    # 以图片中心缩放图片
    def narrowByCenter(self):
        pmapshowarearect = self.pmapShowAreaRect.getRect()
        pmaprect = self.pmapRect.getRect()
        if pmapshowarearect[2] >= pmaprect[2] or pmapshowarearect[3] >= pmaprect[3]:
            return

        self.pmapShowAreaRect.adjust(-self.pmapShowAreaRect.width() * self.scaleRate / (1 - 2 * self.scaleRate), -self.pmapShowAreaRect.height() * self.scaleRate / (1 - 2 * self.scaleRate),
                           self.pmapShowAreaRect.width() * self.scaleRate / (1 - 2 * self.scaleRate), self.pmapShowAreaRect.height() * self.scaleRate / (1 - 2 * self.scaleRate))
        self.repaint()

    def statusLabel(self, message):
        if self.labelQLabel:
            self.labelQLabel.setText(message)

    def status(self, message, delay=-1):
        if self.statusbar:
            self.statusbar.showMessage(message, delay)

    def labelCoord(self, message):
        if self.labelCoordinates:
            self.labelCoordinates.setText(message)

    def setStatusBar(self, statusbar):
        self.statusbar = statusbar

    def setlabelCoordinates(self, labelCoordinates):
        self.labelCoordinates = labelCoordinates

