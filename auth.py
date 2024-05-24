from sqlitedb import SQLiteDB
import os
import hashlib

class AuthManager:
    def __init__(self, path):
        directory = f".\\{path}"
        if not os.path.exists(directory):
            os.mkdir(directory)
        self.user_db = SQLiteDB(f".\\{path}\\users.db")
        self.user_db.create_table("users", "Username varchar(255)", "Password varchar(255)")

    def add_user(self, username, password):
        if len(self.user_db.select(where=f"username=\"{username}\"")) > 0:
            return f"{username} already exists."
        self.user_db.insert([f"\"{username}\"", f"\"{hashlib.sha256(password.encode()).hexdigest()}\""])
        return f"User {username} Successfully added"

    def authenticate(self, username, password):
        if len(self.user_db.select(where=f"username=\"{username}\" AND password="
                                         f"\"{hashlib.sha256(password.encode()).hexdigest()}\"")) > 0:
            return f"Welcome {username}"
        return "Username or password incorrect."

