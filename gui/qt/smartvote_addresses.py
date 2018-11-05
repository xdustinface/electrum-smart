from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from electrum_smart.i18n import _
from electrum_smart.util import PrintError

class VoteAddressesDialog(QDialog, PrintError):

    def __init__(self, vote_address_list, manager, parent=None):
        super(VoteAddressesDialog, self).__init__(parent)
        self.vote_address_list = vote_address_list
        self.manager = manager
        self.setupUi()
        self.setupAddressList()
        self.checked = True


    def setupUi(self):
        self.setObjectName("VoteAddressesDialog")
        self.resize(900, 500)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.votingPowerLabel = QLabel(self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.votingPowerLabel.sizePolicy().hasHeightForWidth())
        self.votingPowerLabel.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.votingPowerLabel.setFont(font)
        self.votingPowerLabel.setObjectName("votingPowerLabel")
        self.horizontalLayout.addWidget(self.votingPowerLabel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.selectionButton = QPushButton(self)
        self.selectionButton.setObjectName("selectionButton")
        self.selectionButton.clicked.connect(self.select_unselect_all)
        self.horizontalLayout_3.addWidget(self.selectionButton)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.addressTable = QTableWidget(self)
        self.addressTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.addressTable.setObjectName("addressTable")
        self.addressTable.setColumnCount(3)
        self.addressTable.setRowCount(0)
        item = QTableWidgetItem()
        self.addressTable.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem()
        self.addressTable.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem()
        self.addressTable.setHorizontalHeaderItem(2, item)
        self.verticalLayout.addWidget(self.addressTable)
        self.widget_2 = QWidget(self)
        self.widget_2.setMinimumSize(QSize(0, 0))
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QSpacerItem(89, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.button = QPushButton(self.widget_2)
        self.button.setObjectName("button")
        self.button.clicked.connect(self.close)
        self.horizontalLayout_2.addWidget(self.button)
        spacerItem2 = QSpacerItem(88, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.verticalLayout.addWidget(self.widget_2)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, VoteAddressesDialog):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("VoteAddressesDialog", "Change your voting power"))
        self.label.setText(_translate("VoteAddressesDialog", "Selected voting power"))
        self.votingPowerLabel.setText(_translate("VoteAddressesDialog", "0 SMART"))
        self.selectionButton.setText(_translate("VoteAddressesDialog", "(un)select all"))
        item = self.addressTable.horizontalHeaderItem(0)
        item.setText(_translate("VoteAddressesDialog", "Enabled"))
        item = self.addressTable.horizontalHeaderItem(1)
        item.setText(_translate("VoteAddressesDialog", "Voting power"))
        item = self.addressTable.horizontalHeaderItem(2)
        item.setText(_translate("VoteAddressesDialog", "Address"))
        self.button.setText(_translate("VoteAddressesDialog", "Close"))

    def setupAddressList(self):
        avaliable_addresses = self.manager.get_avaliable_vote_addresses()
        selected_addresses = self.vote_address_list

        self.votingPowerLabel.setText("{} SMART".format(self.manager.add_thousands_spaces(self.manager.get_selected_voting_power(selected_addresses))))

        nRows = len(avaliable_addresses)
        nCols = 3
        self.addressTable.setColumnCount(nCols)
        self.addressTable.setRowCount(nRows)
        self.addressTable.verticalHeader().hide()
        self.addressTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.addressTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.addressTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.addressTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        rowIndex = 0
        for addr in avaliable_addresses:

            chkBoxItem = QTableWidgetItem()
            chkBoxItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(Qt.Checked)
            #chkBoxItem.toggled.connect(self.update_selected_addresses) #TODO

            self.addressTable.setItem(rowIndex, 0, chkBoxItem) #Enabled
            self.addressTable.setItem(rowIndex, 1, QTableWidgetItem('{} SMART'.format(self.manager.add_thousands_spaces(avaliable_addresses.get(addr))))) #Voting Power
            self.addressTable.setItem(rowIndex, 2, QTableWidgetItem(addr)) #Address
            rowIndex = rowIndex + 1

        #self.addressTable

    def update_selected_addresses(self):
        a = 1

    def select_unselect_all(self):

        if self.checked == True:
            status = Qt.Unchecked
            self.checked = False
        else:
            status = Qt.Checked
            self.checked = True

        for rowIndex in (0,self.addressTable.rowCount()-1):
            self.addressTable.item(rowIndex, 0).setCheckState(status)



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    VoteAddressesDialog = QDialog()
    ui = VoteAddressesDialog()
    ui.setupUi(self)
    self.show()
    sys.exit(app.exec_())
