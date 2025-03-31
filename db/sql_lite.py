import sqlite3

class DB:
    def __init__(self):
        self.DATABASE = "leads.db"

    def init_db(self):
        with sqlite3.connect(self.DATABASE) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                resume TEXT,
                state TEXT DEFAULT 'PENDING'
            )''')
