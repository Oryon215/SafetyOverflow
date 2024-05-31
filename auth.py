from sqlitedb import SQLiteDB
import os
import hashlib
from main import white_list

class AuthManager:


    """
    manage user authentications
    self.user_db(str) - database object
    """
    def __init__(self, path: str) -> None:
        """
        Constructor
        :param path: database path
        """
        directory = f".\\{path}"
        if not os.path.exists(directory):
            os.mkdir(directory)
        self.user_db = SQLiteDB(f".\\{path}\\users.db")
        self.user_db.create_table("Users", "username varchar(255)", "password varchar(255)")

    def add_user(self, username: str, password) -> str:
        """
        add user to data base
        :param username: username
        :param password: password
        :return: string which details whether the operation was successful
        """
        if len(username) > 255 or len(password) > 255:
            return "Username or password too long."
        if white_list(username) or white_list(password):
            return ""
        if len(self.user_db.select("users", where=f"username=\"{username}\"")) > 0:
            return f"{username} already exists."
        self.user_db.insert("users", [f"\"{username}\"", f"\"{hashlib.sha256(password.encode()).hexdigest()}\""])
        return f"User {username} Successfully added"

    def authenticate(self, username, password):
        """
        authenticate user information
        :param username: username
        :param password: password
        :return: string indicating if the operation was successful
        """
        if len(username) > 255 or len(password) > 255:
            return "Username or password too long."
        if len(self.user_db.select("users", where=f"username=\"{username}\" AND password="
                                         f"\"{hashlib.sha256(password.encode()).hexdigest()}\"")) > 0:
            return f"Welcome {username}"
        return "Username or password incorrect."

