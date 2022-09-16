import requests
from PySide6 import QtCore
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *

class DeckView(QWidget):
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