from datetime import datetime
import sqlite3


class SQLiteDB:
    def __init__(self, filename, tablename=None):
        self.con = sqlite3.connect(filename, check_same_thread=False)
        self.cur = self.con.cursor()
        self.table_name = tablename

    def create_table(self, tablename, *columns):
        try:
            self.table_name = tablename
            query = f"CREATE TABLE {tablename} ({', '.join(columns)})"
            self.cur.execute(query)
            self.con.commit()
        except sqlite3.OperationalError as e:
            print(e)

    def insert(self, values, columns=None):
        col = ''
        if columns is not None:
            col = f'({",".join(columns)})'
        query = f"INSERT INTO {self.table_name}{col} VALUES ({','.join(values)})"
        try:
            self.cur.execute(query)
            self.con.commit()
        except sqlite3.IntegrityError as e:
            print(e)

    def select(self, columns='*', where='1=1'):
        query = f"SELECT {columns} FROM {self.table_name} WHERE {where}"
        try:
            self.cur.execute(query)
        except sqlite3.OperationalError as e:
            print(e)
        return self.cur.fetchall()

    def update(self, columns, values, where='1=1'):
        query = f"UPDATE {self.table_name} SET"
        for i in range(len(columns)):
            query += f" {columns[i]}={values[i]},"
        query = query[:-1]
        query += f" WHERE {where}"
        try:
            self.cur.execute(query)
        except sqlite3.OperationalError as e:
            print(e)
        return self.cur.fetchall()

    def delete(self, where):
        query = f"DELETE FROM {self.table_name} WHERE {where}"
        self.cur.execute(query)
        self.con.commit()
