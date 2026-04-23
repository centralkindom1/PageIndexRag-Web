# PageIndex PyQt5 Desktop Application

This is a PyQt5-based desktop implementation of the PageIndex RAG system. It provides a robust, user-friendly interface for document processing, structural visualization, and intelligent question-answering, compatible with Windows 7 (64-bit) and Python 3.8+.

## Features

- **Document Support**: Process PDF, Markdown, TXT, JSON, CSV, and Word (.docx) files.
- **Structural Visualization**: Interactive tree view of the document's hierarchical structure.
- **Intelligent RAG Chat**: Two-phase reasoning-based retrieval (Tree Search + Answer Generation).
- **Asynchronous Processing**: Background threads for document analysis and LLM interaction to keep the UI responsive.
- **LLM Configuration**: Easy setup for OpenAI-compatible APIs (including DeepSeek).

## Requirements

- Python 3.8 or higher
- Windows 7/10/11 (64-bit)
- PyQt5

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Create a `.env` file in this directory with your API key:
   ```env
   CHATGPT_API_KEY=your_api_key_here
   API_BASE_URL=https://api.deepseek.com
   ```

## How to Run

Execute the `main.py` script:

```bash
python main.py
```

## Usage Guide

1. **Settings**: Go to `File -> Settings` to configure your API Key, Base URL, and Model Name.
2. **Upload**: Click the "Upload" button in the Documents panel to select and process a new file.
3. **View Structure**: Once processing is complete (status: completed), click on the document in the list to load its structure in the Tree Viewer.
4. **Chat**: Ask questions about the document in the Chat panel. The system will first "think" to find relevant nodes, highlight them in the tree, and then generate a streaming answer.

## Project Structure

- `main.py`: Application entry point.
- `core/`: Adapted backend logic for document processing and RAG.
- `ui/`: PyQt5 window and widget implementations.
- `uploads/`: Directory for uploaded files.
- `results/`: Directory for generated document structure JSONs.
