import sqlite3 as sql
import time
import itertools as it

TABLE_NAME = "cards"
DATABASE_NAME = "data.db"
TIMES = {'mi': 60, 'd': 60 * 24, 'mo': 60 * 24 * 30, 'y': 60 * 24 * 365}
INTERVALS = [TIMES['mi'],
             TIMES['mi'] * 10,
             TIMES['d'],
             TIMES['d'] * 3,
             TIMES['d'] * 7,
             TIMES['mo'],
             TIMES['mo'] * 6,
             TIMES['y']]

def flatten(listOfLists):
    "Flatten one level of nesting"
    return it.chain.from_iterable(listOfLists)

def initialize_database(name=DATABASE_NAME):
    db = sql.Connection(name)
    create_table_if_none(db)
    return db

def clean(name, exceptions=''):
    return ''.join(c for c in name if c.isalnum() or c in exceptions)

def _reset_table(db):
    db.execute("drop table {}".format(clean(TABLE_NAME)))
    create_table_if_none(db)
 
def create_table_if_none(db):
    c = "char, pinyin, meaning, last_reviewed_c, time_int_c, " \
             + "last_reviewed_r, time_int_r, times_reviewed"
    query = "create table if not exists {}({})"
    db.execute(query.format(clean(TABLE_NAME), clean(c, ',_')))
    db.commit()

def add_card(db, char, pinyin, meaning):
    to_insert = (char, pinyin, meaning, INTERVALS[0], INTERVALS[0])
    query = "insert into {} values (?, ?, ?, 0, ?, 0, ?, 0)"
    db.execute(query.format(clean(TABLE_NAME)), to_insert)
    db.commit()

class Card:
    def __init__(self, db, row_id, is_char_prompt):
        self.db = db
        self.row_id = row_id
        self.is_char_prompt = is_char_prompt

    def get_prompt(self):
        to_select = clean('char' if self.is_char_prompt else 'meaning')
        query = "select {} from {} where ROWID = ?"
        cursor = db.execute(query.format(to_select, TABLE_NAME), (self.row_id,))
        return cursor.fetchall()[0][0]

    def __repr__(self):
        return "<Card {}>".format(self.get_prompt())


def make_cards(db, ids, is_char_prompt):
    result = []
    for i in ids:
        result.append(Card(db, i, is_char_prompt))
    return result


def get_cards_to_study(db, now=None):
    '''Return an iterable of cards to study'''
    if not now:
        now = time.time()
    query_c = "select ROWID from {} where ? > last_reviewed_c + time_int_c"
    query_r = "select ROWID from {} where ? > last_reviewed_r + time_int_r"
    id_c = db.execute(query_c.format(clean(TABLE_NAME)), (now,)).fetchall()
    id_r = db.execute(query_r.format(clean(TABLE_NAME)), (now,)).fetchall()
    return make_cards(db, flatten(id_c), True) \
            + make_cards(db, flatten(id_r), False)
