import os
import traceback

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from electrum_smart import bitcoin
from electrum_smart.util import PrintError, bfh
from electrum_smart.masternode import MasternodeAnnounce

from .masternode_widgets import *
from electrum_smart.masternode_manager import MasternodeManager
from . import util

class MasternodeModel(QAbstractTableModel):
    """Model for smartnodes."""
    ALIAS = 0
    STATUS = 1
    VIN = 2
    COLLATERAL = 3
    DELEGATE = 4
    ADDR = 5
    PROTOCOL_VERSION = 6
    TOTAL_FIELDS = 7

    def __init__(self, manager, parent=None):
        super(MasternodeModel, self).__init__(parent)
        self.manager = manager
        self.masternodes = self.manager.masternodes

        headers = [
            {Qt.DisplayRole: 'Alias',},
            {Qt.DisplayRole: 'Status',},
            {Qt.DisplayRole: 'Collateral',},
            {Qt.DisplayRole: 'Collateral Key',},
            {Qt.DisplayRole: 'Delegate Key',},
            {Qt.DisplayRole: 'Address',},
            {Qt.DisplayRole: 'Version',},
        ]
        for d in headers:
            d[Qt.EditRole] = d[Qt.DisplayRole]
        self.headers = headers

    def add_masternode(self, masternode, save = True):
        self.beginResetModel()
        self.manager.add_masternode(masternode, save)
        self.endResetModel()

    def remove_masternode(self, alias, save = True):
        self.beginResetModel()
        self.manager.remove_masternode(alias, save)
        self.endResetModel()

    def masternode_for_row(self, row):
        mn = self.masternodes[row]
        return mn

    def import_masternode_conf_lines(self, conf_lines, pw):
        self.beginResetModel()
        num = self.manager.import_masternode_conf_lines(conf_lines, pw)
        self.endResetModel()
        return num

    def columnCount(self, parent=QModelIndex()):
        return self.TOTAL_FIELDS

    def rowCount(self, parent=QModelIndex()):
        return len(self.masternodes)

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role not in [Qt.DisplayRole, Qt.EditRole]: return None
        if orientation != Qt.Horizontal: return None

        data = None
        try:
            data = self.headers[section][role]
        except (IndexError, KeyError):
            pass

        return QVariant(data)

    def data(self, index, role = Qt.DisplayRole):
        data = None
        if not index.isValid():
            return QVariant(data)
        if role not in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole, Qt.FontRole, Qt.BackgroundRole]:
            return None

        mn = self.masternodes[index.row()]
        i = index.column()

        if i == self.ALIAS:
            data = mn.alias
        elif i == self.STATUS:
            status = self.manager.masternode_statuses.get(mn.get_collateral_str())
            data = masternode_status(status)
            if role == Qt.BackgroundRole:
                data = QBrush(QColor(ENABLED_MASTERNODE_BG)) if data[0] else None
            # Return the long description for data widget mappers.
            elif role == Qt.EditRole:
                data = data[2]
            else:
                data = data[1]
        elif i == self.VIN:
            txid = mn.vin.get('prevout_hash', '')
            out_n = str(mn.vin.get('prevout_n', ''))
            addr = mn.vin.get('address', '')
            value = str(mn.vin.get('value', ''))
            scriptsig = mn.vin.get('scriptSig', '')
            if role == Qt.EditRole:
                data = ':'.join([txid, out_n, addr, value, scriptsig])
            elif role == Qt.FontRole:
                data = util.MONOSPACE_FONT
            else:
                if all(attr for attr in [txid, out_n, addr]):
                    data = '%s:%s' % (txid, out_n)
                else:
                    data = ''
        elif i == self.COLLATERAL:
            data = mn.collateral_key
            if role in [Qt.EditRole, Qt.DisplayRole, Qt.ToolTipRole] and data:
                data = bitcoin.public_key_to_p2pkh(bfh(data))
            elif role == Qt.FontRole:
                data = util.MONOSPACE_FONT
        elif i == self.DELEGATE:
            data = mn.delegate_key
            if role in [Qt.EditRole, Qt.DisplayRole, Qt.ToolTipRole] and data:
                data = self.manager.get_delegate_privkey(data)
            elif role == Qt.FontRole:
                data = util.MONOSPACE_FONT
        elif i == self.ADDR:
            data = ''
            if mn.addr.ip:
                data = str(mn.addr)
        elif i == self.PROTOCOL_VERSION:
            data = mn.protocol_version

        return QVariant(data)

    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid(): return False

        mn = self.masternodes[index.row()]
        i = index.column()

        if i == self.ALIAS:
            mn.alias = value
        elif i == self.STATUS:
            return True
        elif i == self.VIN:
            s = value.split(':')
            mn.vin['prevout_hash'] = s[0]
            mn.vin['prevout_n'] = int(s[1]) if s[1] else 0
            mn.vin['address'] = s[2]
            mn.vin['value'] = int(s[3]) if s[3] else 0
            mn.vin['scriptSig'] = s[4]
        elif i == self.COLLATERAL:
            return True
        elif i == self.DELEGATE:
            privkey = value
            pubkey = ''
            try:
                # Import the key if it isn't already imported.
                pubkey = self.manager.import_masternode_delegate(privkey)
            except Exception:
                # Don't fail if the key is invalid.
                pass

            mn.delegate_key = pubkey
        elif i == self.ADDR:
            s = value.split(':')
            mn.addr.ip = s[0]
            mn.addr.port = int(s[1])
        elif i == self.PROTOCOL_VERSION:
            try:
                version = int(value)
            except ValueError:
                return False
            mn.protocol_version = version
        else:
            return False

        self.dataChanged.emit(self.index(index.row(), index.column()), self.index(index.row(), index.column()))
        return True

class MasternodeTab(QWidget):

    """Widget that displays smartnodes."""
    def __init__(self, parent=None):
        super(MasternodeTab, self).__init__(parent)
        self.setupUi()

    def update_nodes(self,wallet,config):
        self.wallet = wallet
        self.config = config
        self.manager = MasternodeManager(self.wallet, self.config)
        self.masternodes = self.manager.masternodes

        headers = [
            {Qt.DisplayRole: 'Alias',},
            {Qt.DisplayRole: 'Status',},
            {Qt.DisplayRole: 'Collateral',},
            {Qt.DisplayRole: 'Collateral Key',},
            {Qt.DisplayRole: 'Delegate Key',},
            {Qt.DisplayRole: 'Address',},
            {Qt.DisplayRole: 'Version',},
        ]
        for d in headers:
            d[Qt.EditRole] = d[Qt.DisplayRole]
        self.headers = headers

        self.model = MasternodeModel(self.manager)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.tableWidgetMySmartnodes.setModel(self.proxy_model)

    def setupUi(self):
        self.setObjectName("SmartnodeList")
        self.resize(811, 457)
        self.setMinimumSize(QSize(0, 0))
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.widget = QWidget(self)
        self.widget.setMinimumSize(QSize(0, 0))
        self.widget.setObjectName("widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.CreateButton = QPushButton(self.widget)
        self.CreateButton.setObjectName("CreateButton")
        self.horizontalLayout.addWidget(self.CreateButton)
        self.EditButton = QPushButton(self.widget)
        self.EditButton.setEnabled(False)
        self.EditButton.setObjectName("EditButton")
        self.horizontalLayout.addWidget(self.EditButton)
        self.RemoveButton = QPushButton(self.widget)
        self.RemoveButton.setEnabled(False)
        self.RemoveButton.setObjectName("RemoveButton")
        self.horizontalLayout.addWidget(self.RemoveButton)
        self.ViewButton = QPushButton(self.widget)
        self.ViewButton.setEnabled(False)
        self.ViewButton.setObjectName("ViewButton")
        self.horizontalLayout.addWidget(self.ViewButton)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_2.addWidget(self.widget)

        self.tableWidgetMySmartnodes = QTableView()
        self.tableWidgetMySmartnodes.setMinimumSize(QSize(695, 0))
        self.tableWidgetMySmartnodes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidgetMySmartnodes.setAlternatingRowColors(True)
        self.tableWidgetMySmartnodes.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidgetMySmartnodes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetMySmartnodes.setObjectName("tableWidgetMySmartnodes")

        self.verticalLayout_2.addWidget(self.tableWidgetMySmartnodes)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.startButton = QPushButton(self)
        self.startButton.setObjectName("startButton")
        self.horizontalLayout_5.addWidget(self.startButton)
        self.startMissingButton = QPushButton(self)
        self.startMissingButton.setObjectName("startMissingButton")
        self.horizontalLayout_5.addWidget(self.startMissingButton)
        self.UpdateButton = QPushButton(self)
        self.UpdateButton.setObjectName("UpdateButton")
        self.horizontalLayout_5.addWidget(self.UpdateButton)
        self.autoupdate_label = QLabel(self)
        self.autoupdate_label.setObjectName("autoupdate_label")
        self.horizontalLayout_5.addWidget(self.autoupdate_label)
        self.secondsLabel = QLabel(self)
        self.secondsLabel.setObjectName("secondsLabel")
        self.horizontalLayout_5.addWidget(self.secondsLabel)
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, SmartnodeList):
        _translate = QCoreApplication.translate
        SmartnodeList.setWindowTitle(_translate("SmartnodeList", "Form"))
        self.CreateButton.setText(_translate("SmartnodeList", "Create Smartnode"))
        self.EditButton.setText(_translate("SmartnodeList", "Edit selected"))
        self.RemoveButton.setText(_translate("SmartnodeList", "Remove selected"))
        self.ViewButton.setText(_translate("SmartnodeList", "View selected"))
        self.tableWidgetMySmartnodes.setSortingEnabled(True)
        self.startButton.setText(_translate("SmartnodeList", "S&tart alias"))
        self.startMissingButton.setText(_translate("SmartnodeList", "Start &MISSING"))
        self.UpdateButton.setText(_translate("SmartnodeList", "&Update status"))
        self.autoupdate_label.setText(_translate("SmartnodeList", "Status will be updated automatically in (sec):"))
        self.secondsLabel.setText(_translate("SmartnodeList", "0"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.exit(app.exec_())
