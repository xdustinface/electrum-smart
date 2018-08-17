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
    ADDR = 1
    PROTOCOL_VERSION = 2
    STATUS = 3
    COLLATERAL = 4
    DELEGATE = 5
    VIN = 6
    TOTAL_FIELDS = 7

    def __init__(self, manager, parent=None):
        super(MasternodeModel, self).__init__(parent)
        self.manager = manager
        self.masternodes = self.manager.masternodes

        headers = [
            {Qt.DisplayRole: 'Alias',},
            {Qt.DisplayRole: 'Address', },
            {Qt.DisplayRole: 'Protocol', },
            {Qt.DisplayRole: 'Status',},
            {Qt.DisplayRole: 'Payee', },
            {Qt.DisplayRole: 'Smartnode Key', },
            {Qt.DisplayRole: 'Transaction',},
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

class MasternodeWidget(QWidget):
    """Widget that displays smartnodes."""
    def __init__(self, manager, parent=None):
        super(MasternodesWidget, self).__init__(parent)
        self.manager = manager
        self.model = MasternodesModel(self.manager)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.view = QTableView()
        self.view.setModel(self.proxy_model)
        for header in [self.view.horizontalHeader(), self.view.verticalHeader()]:
            header.setHighlightSections(False)

        header = self.view.horizontalHeader()
        header.setSectionResizeMode(MasternodesModel.ALIAS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(MasternodesModel.VIN, QHeaderView.Stretch)
        header.setSectionResizeMode(MasternodesModel.COLLATERAL, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(MasternodesModel.DELEGATE, QHeaderView.ResizeToContents)
        self.view.verticalHeader().setVisible(False)

        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(self.model.ALIAS, Qt.AscendingOrder)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.view)
        self.setLayout(vbox)

    def select_masternode(self, alias):
        """Select the row that represents alias."""
        self.view.clearSelection()
        for i in range(self.proxy_model.rowCount()):
            idx = self.proxy_model.index(i, 0)
            mn_alias = str(self.proxy_model.data(idx))
            if mn_alias == alias:
                self.view.selectRow(i)
                break

    def populate_collateral_key(self, row):
        """Fill in the collateral key for a smartnode based on its collateral output.

        row refers to the desired row in the proxy model, not the actual model.
        """
        mn = self.masternode_for_row(row)
        self.manager.populate_masternode_output(mn.alias)
        # Emit dataChanged for the collateral key.
        index = self.model.index(row, self.model.COLLATERAL)
        self.model.dataChanged.emit(index, index)

    def refresh_items(self):
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def add_masternode(self, masternode, save = True):
        self.model.add_masternode(masternode, save=save)

    def remove_masternode(self, alias, save = True):
        self.model.remove_masternode(alias, save=save)

    def masternode_for_row(self, row):
        idx = self.proxy_model.mapToSource(self.proxy_model.index(row, 0))
        return self.model.masternode_for_row(idx.row())

    def import_masternode_conf_lines(self, conf_lines, pw):
        return self.model.import_masternode_conf_lines(conf_lines, pw)

class MasternodeTab(QWidget):
    """GUI for smartnodes tab ."""

    def __init__(self, parent=None):
        super(MasternodeTab, self).__init__(parent)
        self.create_layout()

    def update_nodelist(self, wallet, config):
        self.wallet = wallet
        self.config = config
        self.manager = MasternodeManager(self.wallet, self.config)
        self.masternodes = self.manager.masternodes
        self.model = MasternodeModel(self.manager)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.tableWidgetMySmartnodes.setModel(self.proxy_model)

        header = self.tableWidgetMySmartnodes.horizontalHeader()
        header.setSectionResizeMode(MasternodeModel.ALIAS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(MasternodeModel.ADDR, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(MasternodeModel.COLLATERAL, QHeaderView.Stretch)
        header.setSectionResizeMode(MasternodeModel.VIN, QHeaderView.Stretch)
        header.setSectionResizeMode(MasternodeModel.DELEGATE, QHeaderView.Stretch)

        #self.tableWidgetMySmartnodes.selectionModel().selectionChanged.connect(self.on_view_selection_changed)

    def setup_nodelist(self):
        self.tableWidgetMySmartnodes = QTableView()
        self.tableWidgetMySmartnodes.setMinimumSize(QSize(695, 0))
        self.tableWidgetMySmartnodes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidgetMySmartnodes.setAlternatingRowColors(True)
        self.tableWidgetMySmartnodes.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidgetMySmartnodes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetMySmartnodes.setSortingEnabled(True)
        self.tableWidgetMySmartnodes.verticalHeader().setVisible(False)
        self.tableWidgetMySmartnodes.setObjectName("tableWidgetMySmartnodes")

    def create_layout(self):
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
        self.setup_nodelist()
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

    def on_view_selection_changed(self, selected, deselected):
        """Update the data widget mapper."""
        row = 0
        try:
            row = selected.indexes()[0].row()
        except Exception:
            pass
        self.mapper.setCurrentIndex(row)
        self.update_mappers_index()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.exit(app.exec_())
