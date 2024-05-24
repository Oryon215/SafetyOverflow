from sqlitedb import SQLiteDB
import os
from logger import *
from datetime import datetime


class ThreadManager:
    SEPARATOR = "$"

    def __init__(self, path):
        directory = f".\\{path}"
        if not os.path.exists(directory):
            os.mkdir(directory)
            with open(f".\\{path}\\constants", "w") as f:
                f.write("THREAD_COUNT=0\nSTRING_TABLE_INDEX=0")
        self.db_path = path
        self.threads_db = SQLiteDB(f".\\{path}\\threads.db")
        self.threads_db.create_table("Threads", "name varchar(255)", "thread_index int", "date DateTime")
        with open(f"./{path}/constants", "r") as f:
            lines = f.read().split("\n")
            self.thread_count = int(lines[0].split("=")[1])
            self.string_table_index = int(lines[1].split("=")[1])
        self.logger_db = Logger(".\\log\\db.log", logging.INFO)
        open(f".\\{path}\\text", 'a')
        directory = f".\\{path}\\threads_index_table"
        if not os.path.exists(directory):
            os.mkdir(directory)

    def get_index_thread(self, thread_name):
        index = -1
        res = self.threads_db.select("thread_index", f"name=\"{thread_name}\"")
        if len(res) > 0:
            index = self.threads_db.select("thread_index", f"name=\"{thread_name}\"")[0][0]
        return int(index)

    def create_thread(self, thread_name):
        if len(self.threads_db.select("thread_index", f"name=\"{thread_name}\"")) > 0:
            self.logger_db.log("Thread Name already exists.", logging.WARNING)
            return
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        self.threads_db.insert([f"\"{thread_name}\"", str(self.thread_count), f"\"{dt_string}\""])
        thread_db = SQLiteDB(f"{self.db_path}\\threads_index_table\\{self.thread_count}.db")
        thread_db.create_table(f"thread_{self.thread_count}", "string_table_index Int", "author varchar(255)", "date DATETIME", "father Int")
        self.thread_count += 1

    def write_to_thread(self, thread_name, msg, author, father=-1):
        index = self.get_index_thread(thread_name)
        if index >= 0:
            thread_db = SQLiteDB(f"{self.db_path}\\threads_index_table\\{index}.db", f"thread_{index}")
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            thread_db.insert([str(self.string_table_index), f"\"{author}\"", f"\"{dt_string}\"", str(father)])
            with open(f".\\{self.db_path}\\text", 'a') as text:
                text.write(f"{msg}{ThreadManager.SEPARATOR}")
                self.string_table_index += 1
        else:
            self.create_thread(thread_name)
            self.write_to_thread(thread_name, msg, author, father)
        return "Thread Written Successfully."

    def read_thread(self, thread_name):
        index = self.get_index_thread(thread_name)
        if index >= 0:
            thread_db = SQLiteDB(f"{self.db_path}\\threads_index_table\\{index}.db", f"thread_{index}")
            thread = f"{thread_name}:\n\t"
            rows = thread_db.select()
            i = 0
            for row in rows:
                thread += f"{i}: Author:{row[1]}\n\t"
                thread += f"Time:{row[2]}\n\t"
                if row[3] != -1:
                    thread += f"Quoted:{self.read_from_text(rows[row[3]][0])}\n\t"
                thread += self.read_from_text(row[0]) + "\n\t"
                thread += "\n\t"
                i += 1
            return thread
        self.logger_db.log("Cannot find thread.", logging.WARNING)
        return ""

    def read_from_text(self, index):
        with open(f"{self.db_path}\\text", 'r') as text:
            lines = text.read()
            return lines.split(ThreadManager.SEPARATOR)[index]

    def commit(self):
        with open("database/constants", "w") as f:
            f.write(f"THREAD_COUNT={self.thread_count}\nSTRING_TABLE_INDEX={self.string_table_index}")

    def list_threads(self):
        thread = "Threads:\n\t"
        rows = self.threads_db.select()
        for row in rows:
            thread += f"{row[0]} \n\t(Published at:{row[2]}).\n"
        return thread



if __name__ == "__main__":
    m = ThreadManager("database")
    m.write_to_thread("Inon", "Ok", "yuno", -1)
    print(m.list_threads())
    m.commit()

