from base64 import b64encode
from datetime import datetime
import os
import traceback

from PyQt5.QtGui import *
from PyQt5.QtCore import *

from electrum_smart import bitcoin
from electrum_smart.i18n import _
from electrum_smart.masternode import MasternodeAnnounce
from electrum_smart.masternode_manager import parse_masternode_conf
from electrum_smart.util import PrintError, bfh

from .masternode_widgets import *
from . import util

from electrum_smart import constants

import ecdsa
from lib.bitcoin import (generator_secp256k1, EncodeBase58Check, DecodeBase58Check, BitcoinException)
from electrum_smart import constants

SMARTNODE_MIN_VERSION = '90026'
SMARTNODE_DEFAULT_PORT = '9678'

class MasternodeControlDialog(QDialog, PrintError):

    def __init__(self, manager, mapper, model, action, selectedSmartnode, parent):
        super(MasternodeControlDialog, self).__init__(parent)
        self.gui = parent
        self.manager = manager
        self.mapper = mapper
        self.model = model
        self.action = action
        self.selectedSmartnode = selectedSmartnode
        self.setWindowTitle(_('Smartnode Manager'))

        self.waiting_dialog = None
        self.setupUi()

        self.setup_smartnodekey_label()
        self.scan_for_outputs(True)

        if (self.action == 'VIEW'):
            self.fill_smartnode_info()
            self.collateralView.removeWidget(self.stackedWidgetPage1)
            self.customSmartnodeKeyButton.hide()
            self.ipField.setDisabled(True)
            self.aliasField.setDisabled(True)
            self.viewButtonBox.show()
            self.defaultButtonBox.hide()

        elif (self.action == 'EDIT'):
            self.fill_smartnode_info()
            self.add_current_output()
            self.collateralView.removeWidget(self.page)

        elif (self.action == 'CREATE'):
            self.collateralView.removeWidget(self.page)

    def setupUi(self):
        self.setObjectName("SmartnodeControlDialog")
        self.resize(900, 500)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout.setObjectName("verticalLayout")

        # Alias and IP
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.ipField = QLineEdit(self)
        self.ipField.setAlignment(Qt.AlignCenter)
        self.ipField.setObjectName("ipField")
        self.gridLayout.addWidget(self.ipField, 1, 1, 1, 1)
        self.aliasField = QLineEdit(self)
        self.aliasField.setAlignment(Qt.AlignCenter)
        self.aliasField.setObjectName("aliasField")
        self.gridLayout.addWidget(self.aliasField, 0, 1, 1, 1)
        self.label_3 = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.label_2 = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 1)
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        # List or view collateral
        self.collateralView = QStackedWidget(self)
        self.collateralView.setObjectName("collateralView")
        self.create_collateral_list_table()
        self.create_collateral_view_table()
        self.verticalLayout.addWidget(self.collateralView)

        # Smartnode Key
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_5 = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout.addWidget(self.label_5)
        self.smartnodeKeyLabel = QLabel(self)
        font = QFont()
        self.smartnodeKeyLabel.setFont(font)
        self.smartnodeKeyLabel.setStyleSheet("color: rgb(120, 18, 25);")
        self.smartnodeKeyLabel.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.smartnodeKeyLabel.setObjectName("smartnodeKeyLabel")
        self.horizontalLayout.addWidget(self.smartnodeKeyLabel)

        #Copy Smartnode Key Button
        spacerItem7 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem7)
        self.copySmartnodeKeyButton = QPushButton(self)
        self.copySmartnodeKeyButton.setObjectName("copySmartnodeKeyButton")
        self.horizontalLayout.addWidget(self.copySmartnodeKeyButton)
        self.copySmartnodeKeyButton.clicked.connect(self.copy_smartnodekey_label)

        # Custom Smartnode Key Button
        self.customSmartnodeKeyButton = QPushButton(self)
        self.customSmartnodeKeyButton.setObjectName("customSmartnodeKeyButton")
        self.horizontalLayout.addWidget(self.customSmartnodeKeyButton)
        self.customSmartnodeKeyButton.clicked.connect(self.custom_smartnode_key)

        # Smartnode Message
        spacerItem8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem8)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.label_6 = QLabel(self)
        font = QFont()
        font.setItalic(True)
        self.label_6.setFont(font)
        self.label_6.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignTop)
        self.label_6.setWordWrap(True)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_2.addWidget(self.label_6)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        spacerItem9 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem9)

        # Close Button
        self.viewButtonBox = QDialogButtonBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.viewButtonBox.sizePolicy().hasHeightForWidth())
        self.viewButtonBox.setSizePolicy(sizePolicy)
        self.viewButtonBox.setOrientation(Qt.Horizontal)
        self.viewButtonBox.setStandardButtons(QDialogButtonBox.Close)
        self.viewButtonBox.setObjectName("viewButtonBox")
        self.verticalLayout.addWidget(self.viewButtonBox)
        self.viewButtonBox.hide()
        self.viewButtonBox.clicked.connect(self.close)

        # Apply or Cancel
        self.defaultButtonBox = QDialogButtonBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.defaultButtonBox.sizePolicy().hasHeightForWidth())
        self.defaultButtonBox.setSizePolicy(sizePolicy)
        self.defaultButtonBox.setOrientation(Qt.Horizontal)
        self.defaultButtonBox.setStandardButtons(QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
        self.defaultButtonBox.setObjectName("defaultButtonBox")
        self.verticalLayout.addWidget(self.defaultButtonBox)
        self.defaultButtonBox.clicked.connect(self.handle_apply_cancel)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)
        self.setTabOrder(self.aliasField, self.ipField)
        self.setTabOrder(self.ipField, self.collateralTable)
        self.setTabOrder(self.collateralTable, self.copySmartnodeKeyButton)

    def fill_smartnode_info(self):
        self.addressViewLabel.setText(self.selectedSmartnode.vin.get('address', ""))
        self.txIndexViewLabel.setText(str(self.selectedSmartnode.vin.get('prevout_n', "")))
        self.txHashViewLabel.setText(self.selectedSmartnode.vin.get('prevout_hash', ""))
        self.ipField.setText(str(self.selectedSmartnode.addr))
        self.aliasField.setText(self.selectedSmartnode.alias)
        self.smartnodeKeyLabel.setText(self.manager.get_delegate_privkey(self.selectedSmartnode.delegate_key))

    def create_collateral_list_table(self):
        self.stackedWidgetPage1 = QWidget()
        self.stackedWidgetPage1.setObjectName("stackedWidgetPage1")
        self.verticalLayout_3 = QVBoxLayout(self.stackedWidgetPage1)
        self.verticalLayout_3.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_4 = QLabel(self.stackedWidgetPage1)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_3.addWidget(self.label_4)
        self.collateralTable = QTableWidget(self.stackedWidgetPage1)
        font = QFont()
        self.collateralTable.setFont(font)
        self.collateralTable.setColumnCount(3)
        self.collateralTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.collateralTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.collateralTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.collateralTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.collateralTable.horizontalHeader().hide()
        self.collateralTable.verticalHeader().hide()
        self.collateralTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.collateralTable.setObjectName("collateralTable")
        self.collateralTable.setSortingEnabled(False)
        self.verticalLayout_3.addWidget(self.collateralTable)
        self.collateralView.addWidget(self.stackedWidgetPage1)

    def create_collateral_view_table(self):
        self.page = QWidget()
        self.page.setObjectName("page")
        self.verticalLayout_4 = QVBoxLayout(self.page)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setSpacing(10)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        spacerItem2 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.verticalLayout_4.addItem(spacerItem2)
        self.label_7 = QLabel(self.page)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_4.addWidget(self.label_7)
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.addressViewLabel = QLabel(self.page)
        self.addressViewLabel.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.addressViewLabel.setObjectName("addressViewLabel")
        self.gridLayout_2.addWidget(self.addressViewLabel, 0, 1, 1, 1)
        self.label_8 = QLabel(self.page)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.gridLayout_2.addWidget(self.label_8, 0, 0, 1, 1)
        self.txIndexViewLabel = QLabel(self.page)
        self.txIndexViewLabel.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.txIndexViewLabel.setObjectName("txIndexViewLabel")
        self.gridLayout_2.addWidget(self.txIndexViewLabel, 2, 1, 1, 1)
        self.label_9 = QLabel(self.page)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.gridLayout_2.addWidget(self.label_9, 1, 0, 1, 1)
        self.txHashViewLabel = QLabel(self.page)
        self.txHashViewLabel.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.txHashViewLabel.setObjectName("txHashViewLabel")
        self.gridLayout_2.addWidget(self.txHashViewLabel, 1, 1, 1, 1)
        self.label_10 = QLabel(self.page)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.gridLayout_2.addWidget(self.label_10, 2, 0, 1, 1)
        spacerItem3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem3, 0, 2, 1, 1)
        spacerItem4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem4, 2, 2, 1, 1)
        spacerItem5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem5, 1, 2, 1, 1)
        self.verticalLayout_4.addLayout(self.gridLayout_2)
        spacerItem6 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem6)
        self.collateralView.addWidget(self.page)

    def retranslateUi(self, SmartnodeControlDialog):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("SmartnodeControlDialog", "Create new Smartnode"))
        self.ipField.setPlaceholderText(_translate("SmartnodeControlDialog", "000.000.000.000"))
        self.aliasField.setPlaceholderText(_translate("SmartnodeControlDialog", "MyNode1"))
        self.label_3.setText(_translate("SmartnodeControlDialog", "IP-Address"))
        self.label_2.setText(_translate("SmartnodeControlDialog", "Alias"))
        self.label_4.setText(_translate("SmartnodeControlDialog", "Select a collateral for your new node"))
        self.label_7.setText(_translate("SmartnodeControlDialog", "Collateral"))
        self.addressViewLabel.setText(_translate("SmartnodeControlDialog", "0000000000000000000000000"))
        self.label_8.setText(_translate("SmartnodeControlDialog", "Address"))
        self.txIndexViewLabel.setText(_translate("SmartnodeControlDialog", "1"))
        self.label_9.setText(_translate("SmartnodeControlDialog", "Transaction hash"))
        self.txHashViewLabel.setText(
            _translate("SmartnodeControlDialog", "00000000000000000000000000000000000000000000"))
        self.label_10.setText(_translate("SmartnodeControlDialog", "Transaction output id"))
        self.label_5.setText(_translate("SmartnodeControlDialog", "Smartnode Key"))
        self.smartnodeKeyLabel.setText(
            _translate("SmartnodeControlDialog", "00000000000000000000000000000000000000000"))
        self.copySmartnodeKeyButton.setText(_translate("SmartnodeControlDialog", "Copy SmartnodeKey"))
        self.customSmartnodeKeyButton.setText(_translate("SmartnodeControlDialog", "Custom SmartnodeKey"))
        self.label_6.setText(_translate("SmartnodeControlDialog",
                                        "Its required to use the \"Smartnode Key\" above when you install your new node. You can manually insert it into your node\'s smartcash.conf or provide it to the bash installer when prompted."))

    def handle_apply_cancel(self, button):
        sb = self.defaultButtonBox.standardButton(button)
        if sb == QDialogButtonBox.Apply:
            self.save_node()
        elif sb == QDialogButtonBox.Cancel:
            self.close()

    def save_node(self, edit = False):

        alias = self.aliasField.text()
        if not alias:
            QMessageBox.critical(self, _('Error'), _("Alias missing."))
            return

        # Edit Smartnode
        if self.action == 'EDIT':
            self.manager.remove_masternode(self.selectedSmartnode.alias)

        addr = self.get_addr()
        if not addr:
            QMessageBox.critical(self, _('Error'),
                                 _("Invalid IP-Address\n\nRequired format: xxx.xxx.xxx.xxx or xxx.xxx.xxx.xxx:port"))
            return

        collateralTableSelectedItem = self.collateralTable.selectedItems()
        if not collateralTableSelectedItem:
            QMessageBox.critical(self, _('Error'), _("You need to select a collateral."))
            return

        output_index = self.collateralTable.selectedItems()[1].text()
        txId = self.collateralTable.selectedItems()[2].text()
        vin = {'prevout_hash': txId, 'prevout_n': int(output_index)}

        smartnode_privkey = str(self.smartnodeKeyLabel.text())
        if not smartnode_privkey:
            QMessageBox.warning(self, _('Warning'), _('Smartnode privkey is empty.'))
            return

        try:
            smartnode_pubkey = self.manager.import_masternode_delegate(smartnode_privkey)
        except Exception:
            # Show an error if the private key is invalid and not an empty string.
            if smartnode_privkey:
                QMessageBox.warning(self, _('Warning'), _('Ignoring invalid smartnode private key.'))
            delegate_pubkey = ''

        # Create Smartnode
        smartnode = MasternodeAnnounce(alias=alias, vin=vin, delegate_key=smartnode_pubkey, addr=addr)
        self.model.add_masternode(smartnode)
        self.manager.populate_masternode_output(alias)
        self.mapper.submit()
        #self.manager.save()
        self.close()

    def setup_smartnodekey_label(self):
        smartnodeKey = self.generate_smartnode_key()
        self.smartnodeKeyLabel.setText(str(smartnodeKey))

    def copy_smartnodekey_label(self):
        smartnodeKey = self.smartnodeKeyLabel.text()
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(smartnodeKey, mode=cb.Clipboard)

    def custom_smartnode_key(self):
        smartnodeKey, ok = QInputDialog.getText(self, 'Custom Smartnode Key', 'Insert your key here...')
        if ok:
            if self.validate_smartnode_key(smartnodeKey):
                self.smartnodeKeyLabel.setText(str(smartnodeKey))
            else:
                QMessageBox.critical(self, _('Error'), _("Invalid Smartnode Key provided\n\n" + smartnodeKey))

        else:
            return

    def generate_smartnode_key(self):
        G = generator_secp256k1
        _r = G.order()
        pvk = ecdsa.util.randrange(pow(2, 256)) % _r
        privateKey = secret = '%064x'%pvk
        prefix = bytes([constants.net.WIF_PREFIX])
        suffix = b''
        vchIn = prefix + bfh(secret) + suffix
        base58_wif = EncodeBase58Check(vchIn)
        return base58_wif

    def validate_smartnode_key(self, key):
        try:
            vch = DecodeBase58Check(key)
            return True
        except BaseException:
            return False

    def get_addr(self):
        """Get a NetworkAddress instance from this widget's data."""

        ip_field = str(self.ipField.text())
        port = SMARTNODE_DEFAULT_PORT

        if not ip_field:
            return

        ip_port = ip_field.split(':')
        ip = ip_port[0]

        if len(ip_port) > 1:
            port = ip_port[1]

        if self.validate_ip(ip, port):
            return NetworkAddress(ip=ip, port=port)
        else:
            return

    def validate_ip(self, s, p):
        try:
            ip = s.split('.')
            if len(ip) != 4:
                raise Exception('Invalid length')
            for i in ip:
                if int(i) < 0 or int(i) > 255:
                    raise ValueError('Invalid IP byte')
            port = int(p)
        except Exception:
            return False
        return True

    def scan_for_outputs(self, include_frozen):
        """Scan for 10000 SMART outputs.

        If one or more is found, populate the list and enable the sign button.
        """
        self.collateralTable.clear()
        exclude_frozen = not include_frozen
        coins = list(self.manager.get_masternode_outputs(exclude_frozen=exclude_frozen))

        if len(coins) > 0:
            self.add_outputs(coins)

    def add_outputs(self, coins):

        if len(coins) > 0:
            self.collateralTable.horizontalHeader().show()
            self.collateralTable.setRowCount(len(coins))
            self.collateralTable.setHorizontalHeaderLabels(("Address;TX-Index;TX-Hash").split(";"))

            for idx, val in enumerate(coins):
                self.collateralTable.setItem(idx, 0, QTableWidgetItem(val.get('address')))
                self.collateralTable.setItem(idx, 1, QTableWidgetItem(str(val.get('prevout_n'))))
                self.collateralTable.setItem(idx, 2, QTableWidgetItem(val.get('prevout_hash')))

    def add_current_output(self):

        idx = self.collateralTable.rowCount()
        val = self.selectedSmartnode.vin
        self.collateralTable.setRowCount(idx+1)
        self.collateralTable.setItem(idx, 0, QTableWidgetItem(val.get('address')))
        self.collateralTable.setItem(idx, 1, QTableWidgetItem(str(val.get('prevout_n'))))
        self.collateralTable.setItem(idx, 2, QTableWidgetItem(val.get('prevout_hash')))
        self.collateralTable.selectRow(idx)