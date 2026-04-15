from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout
from PyQt5.QtGui import QColor, QIcon, QPixmap

class LegendPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.main_layout.addWidget(self.list)
        self.list.setStyleSheet("border: none;")

    def add_legend_item(self, text, color):
        item = QListWidgetItem(text)
        pix = QPixmap(20, 20)
        pix.fill(QColor(*color))
        item.setIcon(QIcon(pix))
        self.list.addItem(item)

    def set_legend(self, legend_dict):
        self.list.clear()
        for label, color in legend_dict.items():
            self.add_legend_item(label, color)
