import PySide6
from PySide6 import QtCore
from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtWidgets import *
from PySide6.QtGui import QGuiApplication
from backend.config import Backend
import asyncio


class DBBuild(QDialog):
    def __init__(self, parent):
        super(DBBuild, self).__init__(parent)
        self.backend = Backend()
        self.threadpool = QThreadPool()
        self.progress = None
        self.setWindowTitle("Build Database")
        self.setGeometry(100, 100, 400, 400)
        self.layout = QVBoxLayout(self)

        file_finder = QGridLayout()
        cards_text = QLabel()
        cards_button = QPushButton("Select edhrec cards.csv")
        cards_button.clicked.connect(lambda : self.select_file(cards_text, "Select edhrec cards.csv"))
        decks_text = QLabel()
        decks_button = QPushButton("Select edhrec decks.csv")
        decks_button.clicked.connect(lambda: self.select_file(decks_text, "Select edhrec decks.csv"))
        inventory_text = QLabel()
        inventory_button = QPushButton("Select deckbox inventory csv")
        inventory_button.clicked.connect(lambda: self.select_file(inventory_text, "Select deckbox inventory csv"))

        file_finder.addWidget(cards_text, 0, 0)
        file_finder.addWidget(cards_button, 0, 1)
        file_finder.addWidget(decks_text, 1, 0)
        file_finder.addWidget(decks_button, 1, 1)
        file_finder.addWidget(inventory_text, 2, 0)
        file_finder.addWidget(inventory_button, 2, 1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.rejected.connect(self.close)
        self.buttons.accepted.connect(lambda: self.build_db(cards_text.text(), decks_text.text(), inventory_text.text()))

        self.layout.addLayout(file_finder)
        self.layout.addWidget(self.buttons)

    def build_db(self, card_csv, deck_csv, inven_csv):
        progress = QProgressDialog("Building DB...", "Abort", 0, 5, self)
        progress.setMinimumDuration(0)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        self.progress = progress

        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        worker = Worker(self.build_db_thread, card_csv, deck_csv, inven_csv)
        worker.signals.progress.connect(self.progress_fn)
        worker.signals.current_message.connect(self.current_msg_fn)
        self.threadpool.start(worker)

    def progress_fn(self, n):
        self.progress.setValue(n)

    def current_msg_fn(self, msg):
        self.progress.setLabelText(msg + "...")

    def select_file(self, textfield: QLabel, capt):
        filename = QFileDialog.getOpenFileName(self, capt, ".", "CSV Files (*.csv)")
        textfield.setText(filename[0])

    def build_db_thread(self, card_csv, deck_csv, inven_csv, progress_callback, current_message):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        backend = Backend()
        backend.setup_edh_decks(deck_csv, current_message)
        progress_callback.emit(1)
        backend.setup_all_cards(current_message)
        progress_callback.emit(2)
        backend.setup_edh_cards(card_csv, current_message)
        progress_callback.emit(3)
        backend.update_collection(inven_csv, current_message)
        progress_callback.emit(4)
        backend.setup_priced_deck_summary(current_message)
        progress_callback.emit(5)
        return True


class WorkerSignals(QtCore.QObject):
    progress = QtCore.Signal(int)
    current_message = QtCore.Signal(str)


class Worker(QtCore.QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress
        self.kwargs["current_message"] = self.signals.current_message

    @QtCore.Slot()
    def run(self):
        result = self.fn(*self.args, **self.kwargs)

