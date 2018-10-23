from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from electrum_smart.i18n import _
from electrum_smart.util import PrintError


class CastVotesDialog(QDialog, PrintError):

    def __init__(self, parent=None):
        super(CastVotesDialog, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("CastVotesDialog")
        self.resize(900, 500)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout.setObjectName("verticalLayout")
        self.results = QTextBrowser(self)
        self.results.setFrameShape(QFrame.NoFrame)
        self.results.setFrameShadow(QFrame.Plain)
        self.results.setObjectName("results")
        self.verticalLayout.addWidget(self.results)
        self.widget_2 = QWidget(self)
        self.widget_2.setMinimumSize(QSize(0, 0))
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QSpacerItem(89, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.button = QPushButton(self.widget_2)
        self.button.setObjectName("button")
        self.horizontalLayout_2.addWidget(self.button)
        spacerItem1 = QSpacerItem(88, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addWidget(self.widget_2)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, CastVotesDialog):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("CastVotesDialog", "Cast Vote"))
        self.results.setHtml(_translate("CastVotesDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600; color:#000000;\">Start voting...</span></p></body></html>"))
        self.button.setText(_translate("CastVotesDialog", "Cancel"))


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    _CastVotesDialog = QDialog()
    ui = CastVotesDialog()
    ui.setupUi(self)
    self.show()
    sys.exit(app.exec_())
