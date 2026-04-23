import os
import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QSplitter, QMessageBox, QStatusBar)
from PyQt5.QtCore import Qt
from pathlib import Path

from .DocumentManager import DocumentManager
from .TreeViewer import TreeViewer
from .ChatInterface import ChatInterface
from .SettingsDialog import SettingsDialog
from .WorkerThreads import DocumentProcessorThread, ChatWorkerThread
from core.document_service import DocumentService
from core.tree_manager import TreeManager
from core.chat_service import ChatService
from core.converter import SUPPORTED_EXTENSIONS, get_file_type

class MainWindow(QMainWindow):
    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = Path(root_dir)
        self.setWindowTitle("PageIndex PyQt5")
        self.setMinimumSize(1200, 800)

        # Config
        self.config_path = self.root_dir / "app_config.json"
        self.config = self.load_config()

        # Services
        self.uploads_dir = self.root_dir / "uploads"
        self.results_dir = self.root_dir / "results"
        self.doc_service = DocumentService(self.uploads_dir, self.results_dir)
        self.tree_manager = TreeManager(self.results_dir)

        self.current_doc_id = None
        self.processing_threads = {}

        self.init_ui()

    def load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return json.load(f)
        return {
            "api_key": os.getenv("CHATGPT_API_KEY", ""),
            "base_url": os.getenv("API_BASE_URL", ""),
            "model": "deepseek-chat"
        }

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)

    def init_ui(self):
        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        settings_action = file_menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Splitter for flexible layout
        splitter = QSplitter(Qt.Horizontal)

        # Left: Document List
        self.doc_manager = DocumentManager(self.doc_service)
        self.doc_manager.document_selected.connect(self.on_document_selected)
        self.doc_manager.upload_requested.connect(self.on_upload_requested)
        splitter.addWidget(self.doc_manager)

        # Middle: Tree Viewer
        self.tree_viewer = TreeViewer()
        splitter.addWidget(self.tree_viewer)

        # Right: Chat Interface
        self.chat_interface = ChatInterface()
        self.chat_interface.send_message.connect(self.on_send_message)
        splitter.addWidget(self.chat_interface)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)

        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def show_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            self.save_config()
            self.status_bar.showMessage("Settings saved", 3000)

    def on_upload_requested(self, file_path):
        ext = os.path.splitext(file_path)[1]
        file_type = get_file_type(ext)
        if not file_type:
            QMessageBox.critical(self, "Error", f"Unsupported file type: {ext}")
            return

        doc_id = self.doc_service.generate_id(os.path.basename(file_path))
        meta = {
            "doc_id": doc_id,
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_type": file_type,
            "status": "processing",
            "created_at": time.time()
        }
        import time
        self.doc_service.save_metadata(doc_id, meta)
        self.doc_manager.refresh_list()

        thread = DocumentProcessorThread(
            doc_id, file_path, file_type, self.config,
            self.uploads_dir, self.results_dir
        )
        thread.progress.connect(self.on_process_progress)
        thread.finished.connect(self.on_process_finished)
        self.processing_threads[doc_id] = thread
        thread.start()

    def on_process_progress(self, doc_id, percent, message):
        self.status_bar.showMessage(f"Processing {doc_id}: {message} ({percent}%)")

    def on_process_finished(self, doc_id, success, error_msg):
        meta = self.doc_service.get_document(doc_id)
        if meta:
            meta["status"] = "completed" if success else "failed"
            if not success: meta["error"] = error_msg
            self.doc_service.save_metadata(doc_id, meta)

        self.doc_manager.refresh_list()
        if success:
            self.status_bar.showMessage(f"Finished processing {doc_id}", 5000)
        else:
            QMessageBox.critical(self, "Processing Error", f"Failed to process document {doc_id}:\n{error_msg}")

        if doc_id in self.processing_threads:
            del self.processing_threads[doc_id]

    def on_document_selected(self, doc_id):
        meta = self.doc_service.get_document(doc_id)
        if meta and meta.get("status") == "completed":
            try:
                tree_data = self.tree_manager.load_tree(doc_id)
                self.tree_viewer.display_tree(tree_data)
                self.current_doc_id = doc_id
                self.chat_interface.clear_chat()
                self.chat_interface.append_message("system", f"Switched to: {meta['filename']}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load tree: {e}")
        else:
            self.status_bar.showMessage("Document not ready or failed")

    def on_send_message(self, question):
        if not self.current_doc_id:
            QMessageBox.warning(self, "Warning", "Please select a processed document first.")
            self.chat_interface.finalize_ai_message()
            return

        if not self.config.get("api_key"):
            QMessageBox.warning(self, "Warning", "Please set your API Key in Settings.")
            self.chat_interface.finalize_ai_message()
            return

        chat_service = ChatService(
            self.tree_manager,
            self.config["api_key"],
            self.config["base_url"],
            self.config["model"]
        )

        self.worker = ChatWorkerThread(chat_service, self.current_doc_id, question, self.chat_interface.history)
        self.worker.phase.connect(lambda p, m: self.status_bar.showMessage(m))
        self.worker.thinking.connect(lambda t: self.chat_interface.append_message("thinking", t))
        self.worker.nodes_found.connect(lambda ids, titles: self.tree_viewer.highlight_nodes(ids))
        self.worker.answer_chunk.connect(self.on_answer_chunk)
        self.worker.error.connect(lambda e: QMessageBox.critical(self, "Chat Error", e))
        self.worker.finished.connect(self.on_chat_finished)

        self.chat_started = False
        self.worker.start()

    def on_answer_chunk(self, chunk):
        if not self.chat_started:
            self.chat_interface.start_new_ai_message()
            self.chat_started = True
        self.chat_interface.append_ai_chunk(chunk)

    def on_chat_finished(self, referenced_nodes):
        self.chat_interface.finalize_ai_message()
        self.status_bar.showMessage("Ready")
        # Add to history
        # (Simplified: we should ideally get the full message back)
        # For now, let's just enable the button again
