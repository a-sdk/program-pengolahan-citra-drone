from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView

class PropertyDialog(QDialog):
    def __init__(self, name, metadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Properties - {name}")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        table = QTableWidget(len(metadata), 2)
        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for i, (key, value) in enumerate(metadata.items()):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(str(value)))
            
        layout.addWidget(table)