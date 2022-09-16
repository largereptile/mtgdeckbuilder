from PySide6.QtWidgets import *
from PySide6.QtGui import QGuiApplication
from backend.config import Backend


class DBBuild(QDialog):
    def __init__(self):
        super(DBBuild, self).__init__()
        self.backend = Backend()
        self.setWindowTitle("Build Database")
        self.setGeometry(100, 100, 400, 400)

        # redo this, populate form with file dialog

        self.form = QGroupBox("Files")
        self.form_layout = QFormLayout()
        self.edhrec_decks_line = QLineEdit()
        self.edhrec_cards_line = QLineEdit()
        self.inventory_line = QLineEdit()
        self.form_layout.addRow("EDHREC cards.csv: ", self.edhrec_cards_line)
        self.form_layout.addRow("EDHREC decks.csv: ", self.edhrec_decks_line)
        self.form_layout.addRow("Deckbox Inventory csv ", self.edhrec_cards_line)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.rejected.connect(lambda x: self.close())
        self.buttons.accepted.connect(self.build_db)

        layout = QVBoxLayout()
        layout.addWidget(self.form)
        layout.addWidget(self.buttons)

    def build_db(self):
        print("oh no")
