from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton,
                             QHBoxLayout, QFileDialog, QLabel, QListWidgetItem)
from PyQt5.QtCore import pyqtSignal

class DocumentManager(QWidget):
    document_selected = pyqtSignal(str) # Emits doc_id
    upload_requested = pyqtSignal(str) # Emits file_path

    def __init__(self, doc_service, parent=None):
        super().__init__(parent)
        self.doc_service = doc_service
        self.init_ui()
        self.refresh_list()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Documents"))
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        upload_btn = QPushButton("Upload")
        upload_btn.clicked.connect(self.on_upload)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.on_delete)
        btn_layout.addWidget(upload_btn)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def refresh_list(self):
        self.list_widget.clear()
        metadata = self.doc_service.load_all_metadata()
        for doc_id, meta in metadata.items():
            item = QListWidgetItem(meta.get("filename", doc_id))
            item.setData(32, doc_id) # Store doc_id in UserRole
            status = meta.get("status", "unknown")
            if status == "processing":
                item.setText(item.text() + " (Processing...)")
            elif status == "failed":
                item.setText(item.text() + " (Failed)")
            self.list_widget.addItem(item)

    def on_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "",
            "All Supported (*.pdf *.md *.txt *.json *.csv *.docx);;PDF (*.pdf);;Markdown (*.md *.markdown);;Text (*.txt);;JSON (*.json);;CSV (*.csv);;Word (*.docx)"
        )
        if file_path:
            self.upload_requested.emit(file_path)

    def on_delete(self):
        item = self.list_widget.currentItem()
        if item:
            doc_id = item.data(32)
            self.doc_service.delete_document(doc_id)
            self.refresh_list()

    def on_item_clicked(self, item):
        doc_id = item.data(32)
        self.document_selected.emit(doc_id)
