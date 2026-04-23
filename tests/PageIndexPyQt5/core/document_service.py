import os
import json
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List

class DocumentService:
    def __init__(self, uploads_dir: Path, results_dir: Path):
        self.uploads_dir = uploads_dir
        self.results_dir = results_dir
        self.metadata_file = results_dir / "_metadata.json"
        self.uploads_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    def generate_id(self, filename: str) -> str:
        raw = f"{filename}-{time.time()}"
        return hashlib.md5(raw.encode()).hexdigest()[:8]

    def load_all_metadata(self) -> Dict[str, Any]:
        if self.metadata_file.exists():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_metadata(self, doc_id: str, meta: Dict[str, Any]):
        all_meta = self.load_all_metadata()
        all_meta[doc_id] = meta
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(all_meta, f, ensure_ascii=False, indent=2)

    def delete_document(self, doc_id: str):
        all_meta = self.load_all_metadata()
        if doc_id in all_meta:
            meta = all_meta.pop(doc_id)
            # Try to delete files
            try:
                os.unlink(meta["file_path"])
                os.unlink(self.results_dir / f"{doc_id}.json")
            except: pass
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(all_meta, f, ensure_ascii=False, indent=2)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.load_all_metadata().get(doc_id)
