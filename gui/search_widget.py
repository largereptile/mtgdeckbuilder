import requests
from PySide6 import QtCore
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *
from deckbuilder.config import Backend


class Search(QWidget):
    def __init__(self, tab_widget):
        super().__init__()
        self.tab_widget = tab_widget
        self.precon_field = QCheckBox()
        self.max_price_field = QLineEdit()
        self.commander_field = QLineEdit()
        self.backend = Backend()
        self.current_decks = []
        self.current_deck_widget = None
        self.main_grid = QGridLayout(self)
        search_fields = self.setup_search_fields()
        self.main_grid.addLayout(search_fields, 1, 0)
        self.main_grid.addWidget(QTableWidget())

    def setup_search_fields(self):
        top_hbox = QHBoxLayout()
        commander_label = QLabel()
        commander_label.setText("Commander Name: ")
        max_price_label = QLabel()
        max_price_label.setText("Max Price: ")
        precon_label = QLabel()
        precon_label.setText("Precon Upgrade: ")
        search_button = QPushButton()
        search_button.setText("Search")
        search_button.clicked.connect(self.search_decks)
        top_hbox.addWidget(commander_label)
        top_hbox.addWidget(self.commander_field)
        top_hbox.addWidget(max_price_label)
        top_hbox.addWidget(self.max_price_field)
        top_hbox.addWidget(precon_label)
        top_hbox.addWidget(self.precon_field)
        top_hbox.addWidget(search_button)
        return top_hbox

    def setup_menubar(self):
        menubar = QMenuBar()
        configmenu = QMenu("Config")
        menubar.addMenu(configmenu)
        return menubar

    def setup_table(self, rows, columns, decks):
        headers = ["Commander Name", "url", "Price", "Unowned Cards"]
        table = QTableWidget(rows, 4)
        table.clicked.connect(self.row_click)
        for n, deck in enumerate(decks):
            table.setItem(n, 0, QTableWidgetItem(deck[1]))
            table.setItem(n, 1, QTableWidgetItem(deck[4]))
            table.setItem(n, 2, QTableWidgetItem(str(deck[5] / 100)))
            table.setItem(n, 3, QTableWidgetItem(f"{deck[6]}/{deck[7]}"))
        table.setHorizontalHeaderLabels(headers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        self.main_grid.addWidget(table, 2, 0)

    def search_decks(self):
        commander = self.commander_field.text()
        max_price = int(self.max_price_field.text()) if self.max_price_field.text() else 10000
        precon = self.precon_field.isChecked()
        if commander == "":
            commander = None
        decks = self.backend.find_decks(commander=commander, max_price=max_price, precon=precon)
        self.setup_table(len(decks), 3, decks)
        self.current_decks = decks

    def row_click(self, item):
        deck_index = item.row()
        self.current_deck_widget = DeckInfo(self.current_decks[deck_index], self.backend)
        self.current_deck_widget.resize(1000, 720)
        self.tab_widget.addTab(self.current_deck_widget, "Test")


class DeckInfo(QWidget):
    def __init__(self, deck, backend):
        super().__init__()
        self.pix_map = QPixmap()
        self.img_label = QLabel()
        self.main_vbox = QVBoxLayout(self)

        self.o_cards = []
        self.u_cards = []

        title = QLabel(f"Commander: {deck[1]} | Theme: {deck[3]} | Creation Date: {deck[2]}")
        self.main_vbox.addWidget(title)

        url = QLabel(f"URL: {deck[4]}")
        price = QLabel(f"(Estimated) Price: €{deck[5] / 100}")
        self.main_vbox.addWidget(url)
        self.main_vbox.addWidget(price)

        self.grid = QGridLayout()
        self.cards = QHBoxLayout()
        self.u_cards = backend.get_unowned_cards(deck[0])
        utable = QTableWidget(len(self.u_cards), 4)
        for i, card in enumerate(self.u_cards):
            utable.setItem(i, 0, QTableWidgetItem(card[3]))
            utable.setItem(i, 1, QTableWidgetItem(f"€{card[4] / 100}"))
            utable.setItem(i, 2, QTableWidgetItem(card[8]))
            utable.setItem(i, 3, QTableWidgetItem(card[6]))
        utable.setHorizontalHeaderLabels(["Unowned Card Name", "Price", "Cost", "Colour"])
        header = utable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.o_cards = backend.get_owned_cards(deck[0])
        otable = QTableWidget(len(self.o_cards), 4)
        for i, card in enumerate(self.o_cards):
            otable.setItem(i, 0, QTableWidgetItem(card[3]))
            otable.setItem(i, 1, QTableWidgetItem(f"€{card[4] / 100}"))
            otable.setItem(i, 2, QTableWidgetItem(card[8]))
            otable.setItem(i, 3, QTableWidgetItem(card[6]))
        otable.setHorizontalHeaderLabels(["Owned Cards", "Price", "Cost", "Colour"])
        header = otable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        otable.clicked.connect(self.update_old_image)
        utable.clicked.connect(self.update_new_image)
        self.cards.addWidget(self.img_label)
        self.cards.addWidget(utable)
        self.cards.addWidget(otable)

        self.grid.addLayout(self.cards, 0, 0)
        self.main_vbox.addLayout(self.grid)

    def update_old_image(self, item):
        card_index = item.row()
        request = requests.get(self.o_cards[card_index][7])
        self.pix_map.loadFromData(request.content)
        self.pix_map.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
        self.img_label.setPixmap(self.pix_map)
        self.img_label.setScaledContents(True)

    def update_new_image(self, item):
        card_index = item.row()
        request = requests.get(self.u_cards[card_index][7])
        self.pix_map.loadFromData(request.content)
        self.pix_map.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
        self.img_label.setPixmap(self.pix_map)
        self.img_label.setScaledContents(True)