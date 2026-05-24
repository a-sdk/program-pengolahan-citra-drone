from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QLabel, QTextBrowser
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
        self.info_list = QTextBrowser()
        self.info_list.setReadOnly(True)
        self.info_list.setOpenExternalLinks(True)
        self.info_list.setStyleSheet("QTextBrowser { border: none; }")

        self.main_layout.addWidget(self.legend_list, stretch=1)
        self.main_layout.addWidget(self.info_list, stretch=1)

    def clear(self):
        self.legend_list.clear()
        self.info_list.clear()

    def add_legend_item(self, label, color):
        item = QListWidgetItem(label)
        pix = QPixmap(20, 20)
        pix.fill(QColor(*color))
        item.setIcon(QIcon(pix))
        self.legend_list.addItem(item)

    def _add_rich_info_item(self, text, is_header=False, is_highlight=False):
            # Logika formatting
            if is_header:
                top_margin = "15px" if text.lower() == "recommendation:" else "0px"
                html = (f"<div style='font-weight: bold; font-size: 18px; "
                                f"margin-top: {top_margin}; margin-bottom: 5px; "
                                f"border-bottom: 1px solid #ddd;'>{text}</div>")
            elif is_highlight:
                html = f"<div style='color: #000; margin: 0px; padding: 0px;'>{text}</div>"
            else:
                html = f"<div style='font-size: 16px; margin: 0px; padding: 0px;'>{text}</div>"
            
            self.info_list.append(html)

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
                self._add_rich_info_item(f"{key}: {value:.2f} %")
        self._add_rich_info_item("Recommendation:", is_header=True)
        recom = info_dict.get("rekomendasi", "-")
        self._add_rich_info_item(recom, is_highlight=True)

