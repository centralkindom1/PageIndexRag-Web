from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QHBoxLayout, QMessageBox, QComboBox)

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config # This will be a dict or a manager
        self.setWindowTitle("LLM Settings")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.api_key_input = QLineEdit(self.config.get("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.base_url_input = QLineEdit(self.config.get("base_url", ""))
        self.model_input = QLineEdit(self.config.get("model", "deepseek-chat"))

        form.addRow("API Key:", self.api_key_input)
        form.addRow("Base URL:", self.base_url_input)
        form.addRow("Model Name:", self.model_input)

        layout.addLayout(form)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        self.setLayout(layout)

    def save_settings(self):
        self.config["api_key"] = self.api_key_input.text().strip()
        self.config["base_url"] = self.base_url_input.text().strip()
        self.config["model"] = self.model_input.text().strip()
        self.accept()
