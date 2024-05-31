from enum import *
from thread_manager import *
from auth import AuthManager
import ssl
import threading


class Error(Enum):
    """
    Server Error Enumerator
    """
    MessageTooShort = "Connection at {} closed."
    UnrecognizedProtocol = "Failed to recognize message protocol."
    ParameterCount = "Wrong num of parameters supplied."
    WrongLength = "Length parameter did not match the actual message length."
    ConnectionError = "Connection is no longer valid."
    FileNotFound = "Invalid file path was provided."
    SendFile = "File sending was stopped due to client not answering."


class OPERATIONS(Enum):
    """
    Server Operations Enumerator
    """
    WRITE = "W"
    READ = "R"
    AUTH = "A"
    REGISTER = "RE"
    LIST_THREADS = "LT"
    DOWNLOAD_FILE = "D"
    SERVER_ANSWER = "ANS"
    FILE_RECV = "FR"
    SERVER_ERROR = "E"


class Protocol:
    MINIMUM_SECTIONS = 3  # minimum number of packet components
    SEPARATOR = "\xff"  # packet component separator
    OPERATIONS_PARAMETERS = {OPERATIONS.WRITE: 5, OPERATIONS.READ: 2, OPERATIONS.AUTH: 2,
                             OPERATIONS.REGISTER: 2, OPERATIONS.LIST_THREADS: 0, OPERATIONS.DOWNLOAD_FILE: 3}
    # num of parameters per each operation
    MESSAGE_BODY = 16  # message body index
    CHUNK_SIZE = 1024  # maximum packet size
    FINISH = "DONE"  # finish message

    @staticmethod
    def parse_message(msg: str) -> list:
        """
        Parse Message
        :param msg: packet message
        :return: return packet components (separated by SEPERATOR)
        """
        components = msg.split(Protocol.SEPARATOR)
        error = Protocol.check_error_msg(msg)
        if error is not None:
            return [error]
        return components[2:]

    @staticmethod
    def final_value(msg: str):
        res = Protocol.parse_message(msg)
        if len(res) > 1:
            return res[1]
        else:
            return res[0]

    @staticmethod
    def check_error_msg(msg: str):
        """
        Check if message doesn't match the protocol
        :param msg: packet message
        :return: list with error value if error exists otherwise None
        """
        components = msg.split(Protocol.SEPARATOR)
        if components == ['']:
            return Error.MessageTooShort
        if len(components) < Protocol.MINIMUM_SECTIONS:
            return Error.ParameterCount
        if components[0] != "INON":
            return Error.UnrecognizedProtocol
        if not components[1].isnumeric():
            return Error.UnrecognizedProtocol
        if len(msg[Protocol.MESSAGE_BODY:]) != int(components[1]):
            return Error.WrongLength
        return None

    @staticmethod
    def handle_error(sock: ssl.SSLSocket, logger: Logger, error: Error, info: int = logging.ERROR) -> None:
        """
        Handle Server Error
        :param sock: error socket
        :param logger: logger for documentation
        :param error: error TYPE
        :param info: logging type
        :return: None
        """
        sock.send(Protocol.compile_message(OPERATIONS.SERVER_ERROR, error.value).encode())
        logger.log(error.value, info)

    @staticmethod
    def check_operation_parameters(length: int, sock, logger: Logger, operation: OPERATIONS) -> bool:
        """
        Check if operation parameters match the desired operation
        :param length: length of parameters
        :param sock: client socket
        :param logger: documentation logger
        :param operation: server operation
        :return: True if operation successful and False otherwise
        """
        if length != Protocol.OPERATIONS_PARAMETERS[operation]:
            Protocol.handle_error(sock, logger, Error.ParameterCount)
            return False
        return True

    @staticmethod
    def handle_operation(sock: ssl.SSLSocket, logger: Logger, operation: OPERATIONS, function, components: list) -> None:
        """
        Handle Desired Operation
        :param sock: client socket
        :param logger: documented logger
        :param operation: server operation
        :param function: desired function
        :param components: function parameters
        :return: None
        """
        if Protocol.check_operation_parameters(len(components), sock, logger, operation):
            res = function(*components)
            #print(res)
            try:
                sock.send(Protocol.compile_message(OPERATIONS.SERVER_ANSWER, res).encode())
                logger.log(res, logging.INFO)
            except Exception as e:
                logger.log(e.__str__(), logging.ERROR)

    @staticmethod
    def compile_message(operation: OPERATIONS, *params) -> str:
        """
        Make New Message
        :param operation: desired server operation
        :param params: parameters for operation
        :return: message
        """
        body = Protocol.SEPARATOR.join(params)
        body = Protocol.SEPARATOR.join([operation.value, body])
        length = str(len(body))
        length = (10 - len(length)) * "0" + length
        return Protocol.SEPARATOR.join(["INON", length, body])

    @staticmethod
    def send_file(sock, logger: Logger, filename: str) -> str:
        """
        Send File to client
        :param sock: client socket
        :param logger: documented logger
        :param filename: filename
        :return:
        """
        try:
            if not os.path.exists(f".\\files\\filename"):
                raise FileNotFoundError
            file = open(filename, "rb").read()
        except FileNotFoundError:
            Protocol.handle_error(sock, logger, Error.FileNotFound)
            return Protocol.FINISH
        index = 0
        file_size = len(file)
        while index + Protocol.CHUNK_SIZE < file_size:
            print(index, index + Protocol.CHUNK_SIZE)
            try:
                sock.send(file[index:index + Protocol.CHUNK_SIZE])
            except ssl.SSLEOFError:
                return Protocol.FINISH
            index += Protocol.CHUNK_SIZE
            try:
                packet_msg = sock.recv(1024).decode()
                if packet_msg[0] != OPERATIONS.FILE_RECV:
                    Protocol.handle_error(sock, logger, Error.SendFile)
                    return
                msg = Protocol.final_value(packet_msg)
                if msg == str(index):
                    continue
            except ConnectionResetError or ConnectionAbortedError:
                Protocol.handle_error(sock, logger, Error.ConnectionError)
                return Protocol.FINISH
        sock.send(file[index:])
        return Protocol.FINISH

    @staticmethod
    def recv_file(sock: ssl.SSLSocket) -> bytearray:
        """
        Receive file from server
        :param sock: server socket
        :return: bytearray file content
        """
        file = bytearray()
        msg = sock.recv(Protocol.CHUNK_SIZE)
        i = 0
        while msg != Protocol.compile_message(OPERATIONS.SERVER_ANSWER, "DONE").encode():
            file += msg
            sock.send(Protocol.compile_message(OPERATIONS.FILE_RECV, f"{i}").encode())
            msg = sock.recv(Protocol.CHUNK_SIZE)
            i += Protocol.CHUNK_SIZE
        return file
    """
    db_manager (ThreadManager) - threadmanager database object
    auth_manager (AuthManager) - authentication manager database object
    """
    def __init__(self, path: str, path_users: str) -> None:
        """
        Constructor
        :param path: thread database path
        :param path_users: user database path
        """
        self.db_manager = ThreadManager(path)
        self.auth_manager = AuthManager(path_users)
        self.lock_forum = threading.Lock()

    def business_logic(self, sock: ssl.SSLSocket, msg: str, logger: Logger) -> None:
        """
        Server Business Logic
        :param sock: client socket
        :param msg: client message
        :param logger: documented logger
        :return: None
        """
        components = Protocol.parse_message(msg)
        operation = components[0]
        components = components[1:]
        components = list(filter(lambda x: x != '', components))
        match operation:
            case Error.MessageTooShort:
                sock.close()
                logger.log(Error.MessageTooShort.value.format(sock.getsockname()), logging.INFO)
            case Error.UnrecognizedProtocol:
                Protocol.handle_error(sock, logger, Error.UnrecognizedProtocol)
            case Error.ParameterCount:
                Protocol.handle_error(sock, logger, Error.ParameterCount)
            case Error.WrongLength:
                Protocol.handle_error(sock, logger, Error.WrongLength)
            case OPERATIONS.WRITE.value:
                try:
                    self.lock_forum.acquire()
                    Protocol.handle_operation(sock, logger, OPERATIONS.WRITE, self.db_manager.write_to_thread, components)
                finally:
                    self.lock_forum.release()
            case OPERATIONS.READ.value:
                Protocol.handle_operation(sock, logger, OPERATIONS.READ, self.db_manager.read_thread, components)
            case OPERATIONS.AUTH.value:
                Protocol.handle_operation(sock, logger, OPERATIONS.AUTH, self.auth_manager.authenticate, components)
            case OPERATIONS.REGISTER.value:
                Protocol.handle_operation(sock, logger, OPERATIONS.REGISTER, self.auth_manager.add_user, components)
            case OPERATIONS.LIST_THREADS.value:
                Protocol.handle_operation(sock, logger, OPERATIONS.LIST_THREADS, self.db_manager.list_threads, components)
            case OPERATIONS.DOWNLOAD_FILE.value:
                Protocol.handle_operation(sock, logger, OPERATIONS.DOWNLOAD_FILE, self.send_file, [sock, logger] + components)
        self.db_manager.commit()

