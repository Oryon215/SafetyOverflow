from sqlitedb import SQLiteDB
import os
from logger import *
from datetime import datetime
from main import white_list

class ThreadManager:
    """
    Manager Forum Threads
    SEPARATOR (STATIC) (str) - separate between raw text comments
    db_path (str) - path to database
    thread_db (SQLiteDB) - database object
    thread_count (int) - current count of threads
    string_table_index (int) - comments written so far
    logger_db (Logger) - logger object
    """
    SEPARATOR = "\x01"  # seperator between comments

    def __init__(self, path: str) -> None:
        """
        Constructor
        :param path: database path
        """
        directory = f".\\{path}"
        if not os.path.exists(directory):
            os.mkdir(directory)
            with open(f".\\{path}\\constants", "w") as f:
                f.write("THREAD_COUNT=0\nSTRING_TABLE_INDEX=0")
        self.db_path = path
        self.threads_db = SQLiteDB(f".\\{path}\\threads.db")
        self.threads_db.create_table("Threads", "name varchar(255)", "thread_index int",  "date DateTime")
        with open(f".\\{path}\\constants", "r") as f:
            lines = f.read().split("\n")
            self.thread_count = int(lines[0].split("=")[1])
            self.string_table_index = int(lines[1].split("=")[1])
        self.logger_db = Logger(".\\log\\db.log")
        open(f".\\{path}\\text", 'a')

    def get_index_thread(self, thread_name: str) -> int:
        """
        get the index of thread database
        :param thread_name: thread name
        :return: return index of thread in database\thread_index_table folder

        """
        index = -1
        res = self.threads_db.select("Threads", "thread_index", f"name=\"{thread_name}\"")
        if len(res) > 0:
            index = res[0][0]
        return int(index)

    def create_thread(self, thread_name: str) -> None:
        """
        Create new forum thread
        :param thread_name: name of new thread
        :return: None
        """
        if white_list(thread_name):
            print(thread_name)
            print("in1")
            return
        if len(self.threads_db.select("Threads", "thread_index", f"name=\"{thread_name}\"")) > 0:
            print("in!")
            self.logger_db.log("Thread Name already exists.", logging.WARNING)
            return
        print("in11111")
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        self.threads_db.insert("Threads", [f"\"{thread_name}\"", str(self.thread_count), f"\"{dt_string}\""])
        self.threads_db.create_table(f"thread_{self.thread_count}", "string_table_index Int", "author varchar(255)", "date DATETIME", "father Int")
        self.thread_count += 1

    def write_to_thread(self, thread_name: str, msg: str, author: str, max_size: str = '1024', father: int = -1) -> str:
        """
        write comment to thread or create new thread with first comment
        :param thread_name: name of thread
        :param msg: comment
        :param author: comment author
        :param max_size: max size of the comment section in forum
        :param father: irrelevent currently, maybe add quote feature in the future
        :return: thread comment section (until it reaches max size)
        """
        if len(thread_name) > 40:
            return "Thread name too long."
        if len(msg) > 500:
            return "Message too long."
        if white_list(msg) or white_list(author) or white_list(str(father)):
            return ""
        print(self.thread_not_exist(thread_name))
        if (not self.thread_not_exist(thread_name)) and max_size == '1025':
            return "Thread Name exists already."
        self.create_thread(thread_name)
        index = self.get_index_thread(thread_name)
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        self.threads_db.insert(f"thread_{index}", [str(self.string_table_index), f"\"{author}\"", f"\"{dt_string}\"", str(father)])
        with open(f".\\{self.db_path}\\text", 'a') as text:
            text.write(f"{msg}{ThreadManager.SEPARATOR}")
            self.string_table_index += 1
        return self.read_thread(thread_name, max_size)

    def read_thread(self, thread_name: str, max_size: str = '1024') -> str:
        """
        read comments in thread
        :param thread_name: name of thread
        :param max_size: max size of returned comments
        :return: comments in thread (the comments are limited so that they won't exceed the max size)
        """
        if len(thread_name) > 40:
            return "Thread name too long."
        index = self.get_index_thread(thread_name)
        if index >= 0:
            thread = f"{thread_name}:\n\t"
            rows = self.threads_db.select(f"thread_{index}")
            i = 0
            for row in rows:
                comment = ''
                comment += f"{i}: Author:{row[1]}\n\t"
                comment += f"Time:{row[2]}\n\t"
                if row[3] != -1:
                    comment += f"Quoted:{self.read_from_text(rows[row[3]][0])}\n\t"
                comment += self.read_from_text(row[0]) + "\n\t"
                comment += "\n\t"
                i += 1
                if len(thread) + len(comment) > int(max_size):
                    break
                thread += comment
            return thread
        self.logger_db.log("Cannot find thread.", logging.WARNING)
        return ""

    def read_from_text(self, index: int) -> str:
        """
        return comment content
        :param index: index of commentגודל
        :return: comment string
        """
        with open(f"{self.db_path}\\text", 'r') as text:
            lines = text.read()
            return lines.split(ThreadManager.SEPARATOR)[index]

    def commit(self) -> None:
        """
        save changes in constants
        :return: None
        """
        with open("database/constants", "w") as f:
            f.write(f"THREAD_COUNT={self.thread_count}\nSTRING_TABLE_INDEX={self.string_table_index}")

    def list_threads_rows(self) -> list:
        rows = self.threads_db.select("Threads")
        return rows

    def thread_not_exist(self, name: str) -> bool:
        rows = self.threads_db.select("Threads")
        for row in rows:
            if row[0] == name:
                return False
        return True

    def list_threads(self) -> str:
        """
        list all current existing threads
        :return: a list of all current existing threads and the date they were published)
        """
        thread = "Threads:\n\t"
        rows = self.threads_db.select("Threads")
        for row in rows:
            thread += f"{row[0]} \n\t(Published at:{row[2]}).\n\t"
        print(thread)
        return thread


if __name__ == "__main__":
    m = ThreadManager("database")
    m.write_to_thread("Inon", "Ok", "yuno", '1024', -1)
    print(m.list_threads())
    m.commit()

