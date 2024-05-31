import sqlite3


class DatabaseBridge:
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def search(self, query, fetch_all=True):
        self.cursor.execute(query)
        if fetch_all:
            return self.cursor.fetchall()
        else:
            return self.cursor.fetchone()

    def run_query(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def close(self):
        self.connection.close()
