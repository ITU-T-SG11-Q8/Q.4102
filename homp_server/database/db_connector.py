import pymysql

from config import DATABASE_CONFIG


class DBConnector:
    def __init__(self):
        self.connect = pymysql.connect(host=DATABASE_CONFIG["DB_HOST"], port=DATABASE_CONFIG["DB_PORT"],
                                       db=DATABASE_CONFIG["DB_DATABASE"],
                                       user=DATABASE_CONFIG["DB_USER"], password=DATABASE_CONFIG["DB_PASS"],
                                       charset='utf8', cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.connect.cursor()

    def __del__(self):
        self.connect.close()

    def close(self):
        self.connect.close()

    def commit(self):
        self.connect.commit()

    def rollback(self):
        self.connect.rollback()

    def execute(self, query, args):
        self.cursor.execute(query, args)

    def execute_many(self, query, args):
        self.cursor.executemany(query, args)

    def select_one(self, query, args=None):
        self.cursor.execute(query, args)
        return self.cursor.fetchone()

    def select(self, query, args=None):
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def insert(self, query, args):
        self.execute(query, args)

    def insert_all(self, query, args):
        self.execute_many(query, args)

    def update(self, query, args):
        self.execute(query, args)

    def delete(self, query, args):
        self.execute(query, args)
