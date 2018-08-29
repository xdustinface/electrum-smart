import sys, os, re
import traceback, platform
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from electrum_smart import util


if platform.system() == 'Windows':
    MONOSPACE_FONT = 'Lucida Console'
elif platform.system() == 'Darwin':
    MONOSPACE_FONT = 'Monaco'
else:
    MONOSPACE_FONT = 'monospace'


class SmartvoteTab(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        QtWidgets.QPlainTextEdit.__init__(self, parent)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    smartvote = SmartvoteTab()
    smartvote.show()
    sys.exit(app.exec_())
