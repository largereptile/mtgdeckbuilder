import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import *
from backend.config import Backend
from gui.search_widget import Search
from gui.build_db_widget import DBBuild


class App(QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        self.setWindowTitle("EDH Deckstealer Utility")
        self.backend = Backend()

        menu = self.menuBar()
        file_menu = menu.addMenu("&Configure")

        build_database = QAction("Build Database", self)
        build_database.triggered.connect(self.build_backend_db)

        file_menu.addAction(build_database)

        tab_widget = QTabWidget(self)
        tab_widget.addTab(Search(tab_widget), "Commander Search")
        self.setCentralWidget(tab_widget)

    def build_backend_db(self, s):
        build_window = DBBuild(self)
        build_window.show()


if __name__ == "__main__":
    app = QApplication()
    w = App()
    w.showMaximized()
    sys.exit(app.exec())