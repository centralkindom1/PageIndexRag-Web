import os
import json
import asyncio
from typing import List, Dict, Any, Tuple, AsyncGenerator
from openai import AsyncOpenAI
from .tree_manager import TreeManager

TREE_SEARCH_PROMPT = """You are given a question and a tree structure of a document.
Each node contains a node id, node title, and a corresponding summary.
Your task is to find all nodes that are likely to contain the answer to the question.

Question: {question}

Document tree structure:
{tree_skeleton}

Please reply in the following JSON format:
{{
    "thinking": "<Your thinking process on which nodes are relevant to the question>",
    "node_list": ["node_id_1", "node_id_2"]
}}
Directly return the final JSON structure. Do not output anything else."""

ANSWER_PROMPT = """Based on the following document excerpts, answer the user's question.
Cite the relevant section titles in your answer.

Question: {question}

Document excerpts:
{context}

Provide a comprehensive answer in the same language as the question, based only on the provided excerpts."""

class ChatService:
    def __init__(self, tree_manager: TreeManager, api_key: str, base_url: str, model: str):
        self.tree_manager = tree_manager
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url if base_url else None)

    def _extract_json(self, text: str) -> dict:
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match: text = match.group(1).strip()
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try: return json.loads(match.group())
            except json.JSONDecodeError: pass
        try: return json.loads(text)
        except json.JSONDecodeError: return {"thinking": text, "node_list": []}

    async def run_rag_pipeline(self, document_id: str, question: str, chat_history: List[Dict[str, str]]) -> AsyncGenerator[Tuple[str, Any], None]:
        tree = self.tree_manager.load_tree(document_id)
        skeleton = self.tree_manager.get_skeleton(tree)

        yield ("phase", {"phase": "tree_search", "message": "Searching document tree..."})
        search_prompt = TREE_SEARCH_PROMPT.format(
            question=question,
            tree_skeleton=json.dumps(skeleton["structure"], ensure_ascii=False, indent=2)
        )

        try:
            search_response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": search_prompt}],
                temperature=0,
            )
            search_text = search_response.choices[0].message.content
        except Exception as e:
            yield ("error", {"message": f"Tree search failed: {str(e)}"})
            return

        parsed = self._extract_json(search_text)
        thinking = parsed.get("thinking", "")
        node_ids = parsed.get("node_list", [])
        yield ("thinking", {"content": thinking})

        matched_nodes = self.tree_manager.find_nodes_by_ids(tree, node_ids)
        node_titles = [n.get("title", "Unknown") for n in matched_nodes]
        yield ("nodes_found", {"node_ids": node_ids, "node_titles": node_titles})

        if not matched_nodes:
            yield ("answer_chunk", {"content": "No relevant sections found."})
            yield ("done", {"referenced_nodes": []})
            return

        yield ("phase", {"phase": "generating_answer", "message": f"Generating answer from {len(matched_nodes)} sections..."})
        context_parts = []
        for node in matched_nodes:
            text = node.get("text", node.get("summary", ""))
            title = node.get("title", "Unknown")
            start = node.get("start_index", "?")
            end = node.get("end_index", "?")
            context_parts.append(f"[{title}] (pages {start}-{end}):\n{text}")
        context = "\n\n---\n\n".join(context_parts)

        messages = []
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": ANSWER_PROMPT.format(question=question, context=context)})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield ("answer_chunk", {"content": chunk.choices[0].delta.content})
        except Exception as e:
            yield ("error", {"message": f"Answer generation failed: {str(e)}"})
            return

        yield ("done", {"referenced_nodes": node_ids})
