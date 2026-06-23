from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView

class PropertyDialog(QDialog):
    def __init__(self, name, metadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Properties - {name}")
        self.resize(400, 300)
        hide_list = [
             "Legend", 
             "Stats", 
             "transform", 
             "height", 
             "width", 
             "current_factor", 
             "base_factor", 
             "cache_dir", 
             "is_prediction", 
             "class_col"
             ]
        layout = QVBoxLayout(self)
        filtered_metadata = {k: v for k, v in metadata.items() if k not in hide_list}
        table = QTableWidget(len(filtered_metadata), 2)
        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for i, (key, value) in enumerate(filtered_metadata.items()):
                table.setItem(i, 0, QTableWidgetItem(key))
                table.setItem(i, 1, QTableWidgetItem(str(value)))
            
        layout.addWidget(table)