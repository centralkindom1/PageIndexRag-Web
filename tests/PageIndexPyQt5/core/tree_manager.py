import json
from pathlib import Path
from typing import Optional, List, Union

class TreeManager:
    def __init__(self, results_dir: Path):
        self.results_dir = results_dir

    def load_tree(self, document_id: str) -> dict:
        """Load the full tree JSON from results/."""
        tree_path = self.results_dir / f"{document_id}.json"
        if not tree_path.exists():
            tree_path = self.results_dir / f"{document_id}_structure.json"
        if not tree_path.exists():
            raise FileNotFoundError(f"Tree not found for document: {document_id}")
        with open(tree_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_skeleton(self, tree: dict) -> dict:
        """Return tree with 'text' fields stripped (recursive)."""
        def strip_text(node):
            result = {k: v for k, v in node.items() if k != "text"}
            if "nodes" in result:
                result["nodes"] = [strip_text(child) for child in result["nodes"]]
            return result

        return {
            "doc_name": tree.get("doc_name", ""),
            "structure": [strip_text(n) for n in tree.get("structure", [])]
        }

    def find_nodes_by_ids(self, tree: dict, node_ids: List[str]) -> List[dict]:
        """Find nodes by their IDs, including their text content."""
        results = []
        target_ids = set(node_ids)

        def walk(node):
            if node.get("node_id") in target_ids:
                results.append(node)
            for child in node.get("nodes", []):
                walk(child)

        for top_node in tree.get("structure", []):
            walk(top_node)

        return results

    def get_node_by_id(self, tree: dict, node_id: str) -> Optional[dict]:
        """Get a single node by its ID."""
        nodes = self.find_nodes_by_ids(tree, [node_id])
        return nodes[0] if nodes else None
