from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem,
    QAbstractItemView, QMenu
)


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
        self.tree.setHeaderHidden(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)

    def _create_roots(self):
        self.root_input = QTreeWidgetItem(self.tree, ["Input Data"])
        self.root_result = QTreeWidgetItem(self.tree, ["Hasil Analisis"])
        self.root_input.setExpanded(True)
        self.root_result.setExpanded(True)

    # Menambah layer
    def add_layer(self, name, layer_id):
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.UserRole, layer_id)
        item.setCheckState(0, Qt.Checked)
        self.tree.addTopLevelItem(item)    

    # Toggle visibility (checkbox)
    def on_item_changed(self, item, column):
        layer_id = item.data(0, Qt.UserRole)
        visible = item.checkState(0) == Qt.Checked
        self.viewer.set_visible(layer_id, visible)

    # Update z-order
    def update_z_order(self):
        ids = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            ids.append(item.data(0, Qt.UserRole))

        self.viewer.set_z_order(ids)

    # Context menu
    def _open_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return

        menu = QMenu()
        remove_action = menu.addAction("Remove Layer")
        action = menu.exec_(self.tree.viewport().mapToGlobal(pos))

        if action == remove_action:
            self.remove_layer(item)

    # Menghapus layer
    def remove_layer(self, item):
        data = item.data(0, Qt.UserRole)
        if data:
            self.viewer.remove_layer(data)
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.removeChild(item)

    def remove_selected(self):
        item = self.tree.currentItem()
        layer_id = item.data(0, Qt.UserRole)

        self.viewer.remove_layer(layer_id)
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))

    # Menghubungkan signal
    def _connect_signals(self):
        self.tree.itemChanged.connect(self.on_item_changed)
        self.tree.model().rowsMoved.connect(self.update_z_order)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._open_menu)
    
    # API ke luar
    def add_layer_to_root(self, root, name, layer_id):
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.UserRole, layer_id)
        item.setCheckState(0, Qt.Checked)
        root.addChild(item)

    def add_input_layer(self, name, layer_id):
        self.add_layer_to_root(self.root_input, name, layer_id)

    def add_result_layer(self, name, layer_id):
        self.add_layer_to_root(self.root_result, name, layer_id)

    