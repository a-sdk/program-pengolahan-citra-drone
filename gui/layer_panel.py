from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, 
    QTreeWidget, QTreeWidgetItem,
    QTreeWidgetItemIterator, QAbstractItemView, QMenu
)
import logging

logger = logging.getLogger(__name__)

class LayerPanel(QWidget):
    def __init__(self, parent, viewer):
        super().__init__(parent)
        self.viewer = viewer
        self.layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.layout.addWidget(self.tree)

        self._setup_tree()
        self._create_roots()
        self._connect_signals()

    def _setup_tree(self):
        self.tree.setAcceptDrops(True)
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)

    def _create_roots(self):
        self.root_input = QTreeWidgetItem(self.tree, ["Input Data"])
        self.root_result = QTreeWidgetItem(self.tree, ["Hasil Analisis"])
        self.root_input.setExpanded(True)
        self.root_result.setExpanded(True)

    # Menambah layer
    def add_layer(self, name, layer_id):
        logger.info("Menambah layer")
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.UserRole, layer_id)
        item.setCheckState(0, Qt.Checked)
        self.tree.addTopLevelItem(item)    

    # Toggle visibility (checkbox)
    def on_item_changed(self, item, column):
        layer_id = item.data(0, Qt.UserRole)
        logger.info(f"Mengubah visibilitas layer {layer_id}")
        visible = item.checkState(0) == Qt.Checked
        self.viewer.set_visible(layer_id, visible)

    # Update z-order
    def update_z_order(self):
        logger.info("Sinyal terdeteksi, perbarui z-order")
        ids = []
        iterator = QTreeWidgetItemIterator(self.tree)

        while iterator.value():
            item = iterator.value()
            lid = item.data(0, Qt.UserRole)

            if lid is not None:
                ids.append(lid)
            else:
                if item not in [self.root_input, self.root_result]:
                    logger.warning(f"Item '{item.text(0)}' tidak punya ID di UserRole")
            
            iterator += 1
        
        ids.reverse()
        logger.info(f"Layer IDs di panel: {ids}")
        self.viewer.set_z_order(ids)

    # Context menu
    def _open_menu(self, pos):
        item = self.tree.itemAt(pos)
        logger.info("Membuka menu layer")
        if not item:
            return

        if item and item.data(0, Qt.UserRole) is not None:
            menu = QMenu()
            remove_action = menu.addAction("Remove Layer")
            prop_action = menu.addAction("Properties")

            action = menu.exec_(self.tree.viewport().mapToGlobal(pos))

        if action == remove_action:
            self.remove_layer(item)

        if action == prop_action:
            self._show_properties(item)

    # Menghapus layer
    def remove_layer(self, item):
        logger.info("Menghapus layer")
        data = item.data(0, Qt.UserRole)
        if data:
            self.viewer.remove_layer(data)
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.removeChild(item)

    # Properties layer
    def _show_properties(self, item):
        layer_id = item.data(0, Qt.UserRole)
        name = item.text(0)
        
        metadata = self.viewer.get_metadata(layer_id)
        
        if metadata:
            from gui.dialog_property import PropertyDialog 
            dialog = PropertyDialog(name, metadata, self)
            dialog.exec_()

    # Menghubungkan signal
    def _connect_signals(self):
        # Sinyal drag drop layer
        self.tree.model().rowsInserted.connect(self.update_z_order)
        self.tree.model().rowsRemoved.connect(self.update_z_order)
        self.tree.model().rowsMoved.connect(self.update_z_order)
        self.tree.itemChanged.connect(self.on_item_changed)
        # Menu right-click
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._open_menu)
    
    # API ke luar
    def add_layer_to_root(self, root, name, layer_id):
        item = QTreeWidgetItem(root)
        item.setData(0, Qt.UserRole, layer_id)
        item.setText(0, name)
        item.setCheckState(0, Qt.Checked)
        root.setExpanded(True)
 
        logger.info(f"Berhasil menambah '{name}' dengan ID: {layer_id}")
        return item

    def add_input_layer(self, name, layer_id):
        item = self.add_layer_to_root(self.root_input, name, layer_id)
        self.update_z_order()
        return item
 

    def add_result_layer(self, name, layer_id):
        item = self.add_layer_to_root(self.root_input, name, layer_id)
        self.update_z_order()
        return item
    