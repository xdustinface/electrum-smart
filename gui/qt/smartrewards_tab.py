import sys, os, re
import traceback, platform
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from electrum_smart import util

class SmartrewardsTab(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        QtWidgets.QPlainTextEdit.__init__(self, parent)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    smartrewards = SmartrewardsTab()
    smartrewards.show()
    sys.exit(app.exec_())
