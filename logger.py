import logging
from datetime import datetime


class Logger:
    def __init__(self, filename, level=logging.INFO):
        self.filename = filename
        open(filename, "w")

    def log(self, msg, level=logging.INFO):
        file = open(self.filename, "a")
        match level:
            case logging.WARNING:
                operation = "WARNING"
            case logging.DEBUG:
                operation = "DEBUG"
            case logging.ERROR:
                operation = "ERROR"
            case _:
                operation = "INFO"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        file.write(f"{dt_string} - {level} - {msg}\n")
        file.close()


