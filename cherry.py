import sys
import logging
from PyQt5.QtWidgets import QApplication

from widget.welcomewindow import WelcomeWindow

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO,
                        format='%(filename)s[line:%(lineno)d] %(levelname)s %(message)s')

    app = QApplication(sys.argv)
    welcomeWindow = WelcomeWindow()
    welcomeWindow.show()
    app.exec_()
