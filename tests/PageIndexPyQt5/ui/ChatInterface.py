from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit,
                             QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtCore import pyqtSignal, Qt

class ChatInterface(QWidget):
    send_message = pyqtSignal(str) # Emits question

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.history = []

    def init_ui(self):
        layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(QLabel("Chat"))
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a question...")
        self.input_field.returnPressed.connect(self.on_send)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)
        self.setLayout(layout)

    def on_send(self):
        text = self.input_field.text().strip()
        if text:
            self.append_message("user", text)
            self.send_message.emit(text)
            self.input_field.clear()
            self.send_btn.setEnabled(False)

    def append_message(self, role, content):
        if role == "user":
            self.chat_display.append(f"<b>You:</b> {content}<br>")
        elif role == "assistant":
            # If last message was assistant, we might be streaming
            self.chat_display.append(f"<b>AI:</b> {content}<br>")
        elif role == "thinking":
            self.chat_display.append(f"<i>Thinking: {content}</i><br>")
        elif role == "system":
            self.chat_display.append(f"<span style='color: gray;'>{content}</span><br>")

        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def start_new_ai_message(self):
        self.chat_display.append("<b>AI:</b> ")
        self.cursor = self.chat_display.textCursor()
        self.cursor.movePosition(self.cursor.End)

    def append_ai_chunk(self, chunk):
        self.cursor.insertText(chunk)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def finalize_ai_message(self):
        self.chat_display.append("<br>")
        self.send_btn.setEnabled(True)

    def clear_chat(self):
        self.chat_display.clear()
        self.history = []
        self.send_btn.setEnabled(True)
