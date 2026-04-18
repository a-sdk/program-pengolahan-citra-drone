from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QLabel
from PyQt5.QtGui import QColor, QIcon, QPixmap


class LegendPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)

        # List legenda
        self.legend_list = QListWidget()
        self.legend_list.setStyleSheet("QListWidget { border: none; border-bottom: 1px solid #ccc; }")

        # List info
        self.info_list = QListWidget()
        self.info_list.setStyleSheet("QListWidget { border: none; }")

        self.main_layout.addWidget(self.legend_list, stretch=1)
        self.main_layout.addWidget(self.info_list, stretch=1)

    def clear(self):
        self.legend_list.clear()
        self.info_list.clear()

    def add_legend_item(self, label, color):
        item = QListWidgetItem(label)
        pix = QPixmap(16, 16)
        pix.fill(QColor(*color))
        item.setIcon(QIcon(pix))
        self.legend_list.addItem(item)

    def _add_rich_info_item(self, text, is_header=False, is_highlight=False):
            """Fungsi pembantu untuk membuat item dengan format teks khusus"""
            list_item = QListWidgetItem(self.info_list)
            label = QLabel()
            indent = "&nbsp;&nbsp;" if not is_header else ""
            # Logika formatting
            if is_header:
                formatted_text = f"<b>{text}</b>"
                label.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd; padding: 2px;")
            elif is_highlight:
                formatted_text = f"<span>{indent}{text}</span>"
                label.setStyleSheet("background-color: #d1e8ff; color: #000;")
            else:
                formatted_text = f"<span>{indent}{text}</span>"
                label.setStyleSheet("padding: 1px;")
            label.setText(formatted_text)
        
            self.info_list.addItem(list_item)
            self.info_list.setItemWidget(list_item, label)

    def set_legend(self, legend_dict):
        self.legend_list.clear()
        for value, item in legend_dict.items():
            label = item["label"]
            color = item["color"]
            self.add_legend_item(label, color)

    def set_info(self, info_dict):
        self.info_list.clear()
        self._add_rich_info_item("Information:", is_header=True)
        for key, value in info_dict.items():
            if key.lower() != "rekomendasi":
                self._add_rich_info_item(f"{key}: <b>{value:.2f} %</b>")
        self._add_rich_info_item("Recommendation:", is_header=True)
        recom = info_dict.get("rekomendasi", "-")
        self._add_rich_info_item(recom, is_highlight=True)

