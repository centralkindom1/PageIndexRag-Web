import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
from core.page_index import page_index_main
from core.page_index_md import md_to_tree
from core.converter import Converter
from types import SimpleNamespace
import os
from pathlib import Path

class DocumentProcessorThread(QThread):
    progress = pyqtSignal(str, int, str) # doc_id, percent, message
    finished = pyqtSignal(str, bool, str) # doc_id, success, error_msg

    def __init__(self, doc_id, file_path, file_type, config, uploads_dir, results_dir):
        super().__init__()
        self.doc_id = doc_id
        self.file_path = file_path
        self.file_type = file_type
        self.config = config
        self.uploads_dir = uploads_dir
        self.results_dir = results_dir

    def run(self):
        try:
            self.progress.emit(self.doc_id, 10, "Starting processing...")
            opt = SimpleNamespace(**self.config)

            if self.file_type == "pdf":
                self.progress.emit(self.doc_id, 30, "Analyzing PDF structure...")
                result = page_index_main(self.file_path, opt)
            elif self.file_type == "markdown":
                self.progress.emit(self.doc_id, 30, "Parsing Markdown...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(md_to_tree(
                    self.file_path,
                    model=self.config.get("model"),
                    if_add_node_id="yes",
                    if_add_node_summary="yes"
                ))
            else:
                self.progress.emit(self.doc_id, 20, f"Converting {self.file_type} to Markdown...")
                md_path = str(self.uploads_dir / f"{self.doc_id}_converted.md")
                Converter.convert(self.file_path, md_path, self.file_type)

                self.progress.emit(self.doc_id, 40, "Parsing converted content...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(md_to_tree(
                    md_path,
                    model=self.config.get("model"),
                    if_add_node_id="yes",
                    if_add_node_summary="yes"
                ))
                try: os.unlink(md_path)
                except: pass

            output_path = self.results_dir / f"{self.doc_id}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                import json
                json.dump(result, f, ensure_ascii=False, indent=2)

            self.finished.emit(self.doc_id, True, "")
        except Exception as e:
            self.finished.emit(self.doc_id, False, str(e))

class ChatWorkerThread(QThread):
    phase = pyqtSignal(str, str)
    thinking = pyqtSignal(str)
    nodes_found = pyqtSignal(list, list)
    answer_chunk = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, chat_service, doc_id, question, history):
        super().__init__()
        self.chat_service = chat_service
        self.doc_id = doc_id
        self.question = question
        self.history = history

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_pipeline())

    async def _run_pipeline(self):
        referenced_nodes = []
        async for event_type, data in self.chat_service.run_rag_pipeline(self.doc_id, self.question, self.history):
            if event_type == "phase":
                self.phase.emit(data["phase"], data["message"])
            elif event_type == "thinking":
                self.thinking.emit(data["content"])
            elif event_type == "nodes_found":
                self.nodes_found.emit(data["node_ids"], data["node_titles"])
            elif event_type == "answer_chunk":
                self.answer_chunk.emit(data["content"])
            elif event_type == "error":
                self.error.emit(data["message"])
            elif event_type == "done":
                referenced_nodes = data["referenced_nodes"]

        self.finished.emit(referenced_nodes)
