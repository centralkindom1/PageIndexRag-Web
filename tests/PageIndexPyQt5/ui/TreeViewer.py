from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                             QLineEdit, QLabel)
from PyQt5.QtCore import Qt

class TreeViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Document Structure"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search nodes...")
        self.search_input.textChanged.connect(self.filter_tree)
        layout.addWidget(self.search_input)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Title", "ID", "Pages"])
        self.tree_widget.setColumnWidth(0, 250)
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)

    def display_tree(self, tree_data):
        self.tree_widget.clear()
        structure = tree_data.get("structure", [])
        for node in structure:
            self._add_node(self.tree_widget, node)
        self.tree_widget.expandAll()

    def _add_node(self, parent, node_data):
        title = node_data.get("title", "Unknown")
        node_id = node_data.get("node_id", "")
        start = node_data.get("start_index", "")
        end = node_data.get("end_index", "")
        pages = f"{start}-{end}" if start else ""

        item = QTreeWidgetItem(parent, [title, node_id, pages])
        item.setData(0, Qt.UserRole, node_data)

        for child in node_data.get("nodes", []):
            self._add_node(item, child)

    def filter_tree(self, text):
        items = self.tree_widget.findItems("", Qt.MatchContains | Qt.MatchRecursive)
        for item in items:
            match = text.lower() in item.text(0).lower() or text.lower() in item.text(1).lower()
            item.setHidden(not match)
            if match:
                self._show_parents(item)

    def _show_parents(self, item):
        parent = item.parent()
        if parent:
            parent.setHidden(False)
            self._show_parents(parent)

    def highlight_nodes(self, node_ids):
        # Clear previous highlights
        items = self.tree_widget.findItems("", Qt.MatchContains | Qt.MatchRecursive)
        for item in items:
            item.setBackground(0, Qt.transparent)

        # Highlight new ones
        if not node_ids: return

        for node_id in node_ids:
            found = self.tree_widget.findItems(node_id, Qt.MatchExactly | Qt.MatchRecursive, 1)
            for item in found:
                item.setBackground(0, Qt.yellow)
                self.tree_widget.scrollToItem(item)
