import sqlite3


class SQLiteDB:
    """
    sqlite-db interface
    self.con (Connection) - connection to database
    self.cur (Cursor) - cursor object for editing database
    """
    def __init__(self, filename: str):
        """
        contructor
        :param filename: database file
        """
        self.con = sqlite3.connect(filename, check_same_thread=False)
        self.cur = self.con.cursor()

    def create_table(self, table_name: str, *columns) -> None:
        """
        execute CREATE SQL query
        :param table_name: name of the new table
        :param columns: columns of the table
        :return: None
        """
        try:
            query = f"CREATE TABLE {table_name} ({', '.join(columns)}, PRIMARY KEY({columns[0].split(" ")[0]}))"
            self.cur.execute(query)
            self.con.commit()
        except sqlite3.OperationalError as e:
            # connection being dropped or not being able to connect to the database.
            print(e)

    def insert(self, table_name: str, values: list, columns=None) -> None:
        """
        execute INSERT SQL Query
        :param values: inserted values
        :param columns: table columns
        :param table_name: name of table
        :return: None
        """
        col = ''
        if columns is not None:
            col = f'({",".join(columns)})'
        query = f"INSERT INTO {table_name}{col} VALUES ({','.join(values)})"
        try:
            print(query)
            self.cur.execute(query)
            self.con.commit()
        except sqlite3.IntegrityError as e:
            # integrity of the data affected (duplicate values etc.)
            print(e)

    def select(self, table_name: str, columns: str = '*', where: str = '1=1') -> list:
        """
        execute SQL SELECT Query
        :param columns: selected columns
        :param where: where condition
        :param table_name: name of table
        :return: select QUERY value
        """
        query = f"SELECT {columns} FROM {table_name} WHERE {where}"
        try:
            self.cur.execute(query)
        except sqlite3.OperationalError as e:
            print(e)
        return self.cur.fetchall()

    def update(self, table_name: str, columns: list, values: list, where: str = '1=1') -> list:
        """
        execute UPDATE SQL Query
        :param columns: table columns
        :param values: new values
        :param where: where condition
        :param table_name: name of table
        :return: None
        """
        query = f"UPDATE {table_name} SET"
        for i in range(len(columns)):
            query += f" {columns[i]}={values[i]},"
        query = query[:-1]
        query += f" WHERE {where}"
        try:
            self.cur.execute(query)
        except sqlite3.OperationalError as e:
            print(e)
        return self.cur.fetchall()

    def delete(self, table_name: str, where: str) -> None:
        """
        execute DELETE SQL Query
        :param where: where condition
        :param table_name: name of table
        :return: None
        """
        query = f"DELETE FROM {table_name} WHERE {where}"
        self.cur.execute(query)
        self.con.commit()
