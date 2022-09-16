import collections
import csv
import itertools
import json
import sqlite3
import requests

import scrython


class Backend:
    def __init__(self):
        self.db = sqlite3.connect("../mtg.db")
        self.c = self.db.cursor()

    def setup_edh_decks(self, deck_csv_path):
        self.c.execute(f"DROP TABLE IF EXISTS decks")
        csvreader = csv.reader(open(deck_csv_path, "r", encoding="utf8"))
        first = True
        for x, row in enumerate(csvreader):
            if first:
                first = False
                self.c.execute(f"""create table if not exists decks
                                (
                                    deck_id       integer not null
                                        constraint decks_pk
                                            primary key autoincrement,
                                    commander     text    not null,
                                    creation_date text,
                                    theme         text,
                                    url           text    not null,
                                    total_cards integer,
                                    dprecon integer
                                );
                            """)
                self.c.execute("create index if not exists decks_deck_id_index on decks (deck_id);")
                self.c.execute("create index if not exists decks_deck_url_index on decks (url);")
            else:
                total_cards = int(row[6]) + int(row[7]) + int(row[8]) + int(row[9]) + int(row[10]) + int(row[11])
                self.c.execute(f"INSERT INTO decks VALUES (?, ?, ?, ?, ?, ?, ?)", (x, row[2], row[3], row[14], row[0], total_cards, row[16]))
        self.db.commit()
        return True

    def setup_all_cards(self):
        self.c.execute(f"DROP TABLE IF EXISTS cards")
        self.c.execute("""create table if not exists cards
                    (
                        card_id integer not null
                            constraint cards_pk
                                primary key autoincrement,
                        name    text    not null,
                        price   integer default 0,
                        owned   int     default 0,
                        colour  text,
                        image_url text,
                        cmc    text 
                    );
                """)
        self.c.execute("create index if not exists cards_card_id_index on cards (card_id);")
        self.c.execute("create index if not exists cards_card_name_index on cards (name);")
        default_cards_url = scrython.bulk_data.BulkData().data()[2]["download_uri"]
        default_cards = json.loads(requests.get(default_cards_url).text)
        card_list = collections.defaultdict(list)
        urls = collections.defaultdict(str)
        cmcs = collections.defaultdict(str)
        colours = collections.defaultdict(str)
        for card in default_cards:
            print(card)
            name = card["name"]
            if " // " in name:
                name = name.split(" // ")[0]
            eur = card["prices"]["eur"]
            eur = eur if eur is not None else 0
            usd = card["prices"]["usd"]
            usd = usd if usd is not None else 0
            colours[name] = "".join(card["color_identity"])
            if "cmc" in card:
                cmcs[name] = card["cmc"]
            else:
                cmcs[name] = "0"
            if "image_uris" in card and "normal" in card["image_uris"]:
                urls[name] = card["image_uris"]["normal"]
            else:
                urls[name] = "http://www.hearthcards.net/cards/2f2f58c2.png"
            card_list[name].append(int(float(eur) * 100))
            card_list[name].append(int(float(usd) * 100))

        count = 0
        for name, prices in card_list.items():
            num_nonzero = len([x for x in prices if x > 0])
            price = 0
            if num_nonzero > 0:
                price = sum(prices) / num_nonzero
            self.c.execute("INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?)", (count, name, int(price), 0, colours[name], urls[name], cmcs[name]))
            count += 1

        self.db.commit()
        return True

    def setup_edh_cards(self, card_csv_path):
        self.c.execute(f"DROP TABLE IF EXISTS deck_card")
        self.c.execute(f"DROP TABLE IF EXISTS deck_card_ids")
        csvreader = csv.reader(open(card_csv_path, "r", encoding="utf8"))
        first = True
        for x, row in enumerate(csvreader):
            if first:
                first = False
                self.c.execute(f"CREATE TABLE IF NOT EXISTS deck_card (deck_id, card_id)")
            else:
                if row[1].lower() not in ["island", "mountain", "swamp", "forest", "plains"]:
                    self.c.execute("INSERT INTO deck_card VALUES (?, ?)", (row[0], row[1]))
        print("csv in table")
        self.db.commit()
        self.c.execute("""create table if not exists deck_card_ids
                    (
                        deck_id integer not null,
                        card_id integer not null,
                        constraint deck_card_ids_pk
                            primary key (deck_id, card_id)
                    );
                    """)
        self.c.execute("create index if not exists deck_card_ids_deck_id_card_id_index on deck_card_ids (deck_id, card_id)")
        self.c.execute("INSERT INTO deck_card_ids select decks.deck_id, c.card_id from decks inner join deck_card dc on decks.url = dc.deck_id inner join cards c on c.name = dc.card_id")
        # fix commander not being in some of the decks
        # c.execute("INSERT INTO deck_card_ids select decks.deck_id, c.card_id from decks inner join cards c on decks.commander = c.name")

        self.db.commit()
        return True

    def update_collection(self, csv_name):
        csvreader = csv.reader(open(csv_name, "r", encoding="utf8"))
        first = True
        card_set = set()
        self.c.execute("UPDATE cards SET owned=?", (0,))
        for row in csvreader:
            if first:
                first = False
                continue
            if not row:
                continue
            card_set.add(row[2])
        for card in card_set:
            self.c.execute("UPDATE cards SET owned=? WHERE name=?", (1, card))
        self.db.commit()
        return True

    def setup_priced_deck_summary(self):
        self.c.execute("create table if not exists temp_table (d_id integer, price integer, u_count integer);")
        self.c.execute("""insert into temp_table
                    select dci.deck_id as d_id, sum(price), count(owned)
                    from cards
                        inner join deck_card_ids dci
                            on cards.card_id = dci.card_id
                    where owned = 0
                    group by dci.deck_id;""")
        self.c.execute(f"""create table if not exists deck_collection
                    (
                        deck_id       integer not null
                            constraint decks_pk
                                primary key autoincrement,
                        commander     text    not null,
                        creation_date text,
                        theme         text,
                        url           text    not null,
                        price integer,
                        unowned_cards integer,
                        total_cards integer,
                        dprecon integer
                    );""")
        self.c.execute("""insert into deck_collection
                    select deck_id, commander, creation_date, theme, url, temp.price, temp.u_count, total_cards, dprecon
                    from decks as d
                    inner join temp_table as temp
                    on temp.d_id = d.deck_id""")
        self.c.execute("drop table temp_table")
        self.c.execute("drop table decks")
        print("done decks")
        return True

    def find_decks(self, commander=None, precon=False, max_price=10000):
        if commander:
            decks = self.c.execute(f"select * from deck_collection where commander LIKE ? and total_cards > 50 and price<=? and dprecon{'<20' if precon else '>20'} order by unowned_cards", (f'%{commander}%', max_price)).fetchall()
        else:
            decks = self.c.execute(f"select * from deck_collection where price<=? and total_cards > 50 and dprecon{'<20' if precon else '>20'} order by unowned_cards LIMIT 500", (max_price,)).fetchall()
        return decks

    def get_owned_cards(self, deck_id):
        cards = self.c.execute("select * from deck_card_ids inner join cards on cards.card_id = deck_card_ids.card_id where cards.owned=1 and deck_id=?", (deck_id,)).fetchall()
        return cards

    def get_unowned_cards(self, deck_id):
        cards = self.c.execute("select * from deck_card_ids inner join cards on cards.card_id = deck_card_ids.card_id where cards.owned=0 and deck_id=?", (deck_id,)).fetchall()
        return cards

    def rebuild(self, deck_csv="decks.csv", card_csv="cards.csv", inventory="Inventory_ito_2022.July.08.csv"):
        self.setup_edh_decks(deck_csv)
        self.setup_all_cards()
        self.setup_edh_cards(card_csv)
        self.update_collection(inventory)
        self.setup_priced_deck_summary()
        return True
