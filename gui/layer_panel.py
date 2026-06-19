from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
    QTreeWidget, QTreeWidgetItem,
    QTreeWidgetItemIterator, QAbstractItemView, QMenu
)
import os
import shutil
import logging

logger = logging.getLogger(__name__)

class LayerPanel(QWidget):
    infoMsg = pyqtSignal(str)
    layerSelected = pyqtSignal(int)

    def __init__(self, parent, viewer):
        super().__init__(parent)
        self.viewer = viewer
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.main_layout.addWidget(self.tree)
        self.layer_ids = []
        self._setup_tree()
        self._connect_signals()

    def _setup_tree(self):
        self.tree.setFrameShape(QFrame.NoFrame)
        self.tree.setLineWidth(0)
        self.tree.setStyleSheet("border: none;")
        self.tree.setAcceptDrops(True)
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)

    # Menambah layer
    def add_layer_item(self, layer_id, name):
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.UserRole, layer_id)
        item.setCheckState(0, Qt.Checked)
        self.tree.insertTopLevelItem(0, item)
        self.infoMsg.emit(f"{name} loaded.")
        logger.info(f"Berhasil menambah '{name}' dengan ID: {layer_id}")

    # Toggle visibility (checkbox)
    def on_item_changed(self, item):
        layer_id = item.data(0, Qt.UserRole)
        logger.info(f"Mengubah visibilitas layer {layer_id}")
        is_visible = item.checkState(0) == Qt.Checked
        self.viewer.set_visible(layer_id, is_visible)

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
            
            iterator += 1
        self.layer_ids = ids
        self.layer_ids.reverse()
        logger.info(f"Layer IDs di panel: {self.layer_ids}")
        self.viewer.set_z_order(self.layer_ids)

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

    def on_item_clicked(self, item, col):
        layer_id = item.data(0, Qt.UserRole)
        self.layerSelected.emit(layer_id)
        logger.info(f"Layer {layer_id} diklik")
        
    def remove_layer(self, item):
        layer_id = item.data(0, Qt.UserRole)
        logger.info(f"Menghapus layer {layer_id}")
        layer_name = os.path.splitext(item.text(0))[0]
        if layer_id:
            try:
                if layer_name:
                    from path_config import AppPaths
                    temp_dir = AppPaths.TEMP / layer_name
                    if os.path.exists(temp_dir):
                        shutil.rmtree(str(temp_dir))
                        # logger.info(f"Folder temp dihapus: {temp_dir}")
            except Exception as e:
                logger.error(f"Gagal menghapus: {e}")
            self.viewer.remove_layer(layer_id)
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.removeChild(item)
        self.infoMsg.emit(f"{item.text(0)} removed.")

    # Properties layer
    def _show_properties(self, item):
        layer_id = item.data(0, Qt.UserRole)
        name = item.text(0)
        
        metadata = self.viewer.get_metadata(layer_id)
        
        if metadata:
            from gui.property_dialog import PropertyDialog 
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
        # Layer dipilih
        self.tree.itemClicked.connect(self.on_item_clicked)

    