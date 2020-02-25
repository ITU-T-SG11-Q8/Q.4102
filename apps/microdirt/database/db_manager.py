import pymysql

from config import DATABASE_CONFIG


class DBManager:
    def __init__(self):
        self.database_name = DATABASE_CONFIG["DB_DATABASE"]
        self.connect = pymysql.connect(host=DATABASE_CONFIG["DB_HOST"], port=DATABASE_CONFIG["DB_PORT"],
                                       user=DATABASE_CONFIG["DB_USER"], password=DATABASE_CONFIG["DB_PASS"],
                                       charset='utf8', cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.connect.cursor()

    def __del__(self):
        self.connect.close()

    def init(self):
        try:
            is_execute = False
            self.cursor.execute("SHOW DATABASES LIKE %s", (self.database_name,))
            database = self.cursor.fetchone()
            if database is None:
                is_execute = True
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS {0}".format(self.database_name))
                print("[DBManager] CREATE DATABASE =>", self.database_name)

            self.cursor.execute("USE {0}".format(self.database_name))

            self.cursor.execute("SHOW TABLES LIKE 'fine_dust'")
            hp2p_overlay = self.cursor.fetchone()
            if hp2p_overlay is None:
                is_execute = True
                self.cursor.execute("CREATE TABLE IF NOT EXISTS fine_dust ( "
                                    "data_time DATETIME NOT NULL, "
                                    "pm10_data LONGTEXT NOT NULL COLLATE utf8_unicode_ci, "
                                    "updated_at DATETIME NOT NULL,  "
                                    " PRIMARY KEY (`data_time`)"
                                    ")")
                print("[DBManager] CREATE TABLE fine_dust")

            if is_execute:
                self.connect.commit()
        except Exception as e:
            print(e)
            self.connect.rollback()
            return False
