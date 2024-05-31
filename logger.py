import logging
from datetime import datetime


class Logger:
    """
    log program messages
    self.filename (str): log filename
    """
    def __init__(self, filename: str) -> None:
        """
        constructor
        :param filename: log file
        """
        self.filename = filename
        open(filename, "w")

    def log(self, msg: str, level: int = logging.INFO) -> None:
        """
        document actions
        :param msg: log message
        :param level: log type
        :return: None
        """
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
        file.write(f"{dt_string} - {operation} - {msg}\n")
        file.close()


