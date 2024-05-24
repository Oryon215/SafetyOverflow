from enum import *
from thread_manager import *
from auth import AuthManager

class Error(Enum):
    MessageTooShort = "Connection at {} closed."
    UnrecognizedProtocol = "Failed to recognize message protocol."
    ParameterCount = "Wrong num of parameters supplied."
    WrongLength = "Parameter length did not match the actual message length."
    ConnectionError = "Connection is no longer valid."
    FileNotFound = "Invalid file path was provided."


class OPERATIONS(Enum):
    WRITE = "W"
    READ = "R"
    AUTH = "A"
    REGISTER = "RE"
    LIST_THREADS = "LT"
    DOWNLOAD_FILE = "D"


class Protocol:
    MINIMUM_PARAMETERS = 3
    SEPARATOR = "\xff"
    OPERATIONS_PARAMETERS = {OPERATIONS.WRITE: 4, OPERATIONS.READ: 1, OPERATIONS.AUTH: 2,
                             OPERATIONS.REGISTER: 2, OPERATIONS.LIST_THREADS: 0, OPERATIONS.DOWNLOAD_FILE: 3}
    MESSAGE_BODY = 16
    CHUNK_SIZE = 1024
    FINISH = "DONE"

    @staticmethod
    def parse_message(msg):
        components = msg.split(Protocol.SEPARATOR)
        if components == ['']:
            return [Error.MessageTooShort]
        if len(components) < Protocol.MINIMUM_PARAMETERS:
            return [Error.ParameterCount]
        if components[0] != "INON":
            return [Error.UnrecognizedProtocol]
        if not components[1].isnumeric():
            return [Error.UnrecognizedProtocol]
        if len(msg[Protocol.MESSAGE_BODY:]) != int(components[1]):
            return [Error.WrongLength]
        return components[2:]

    @staticmethod
    def handle_error(sock, logger, error, info=logging.ERROR):
        sock.send(error.value.encode())
        logger.log(error.value, info)

    @staticmethod
    def check_operation_parameters(length, sock, logger, operation):
        if length != Protocol.OPERATIONS_PARAMETERS[operation]:
            Protocol.handle_error(sock, logger, Error.ParameterCount)
            return False
        return True

    @staticmethod
    def handle_operation(sock, logger, operation, function, components):
        if Protocol.check_operation_parameters(len(components), sock, logger, operation):
            res = function(*components)
            print(res)
            sock.send(res.encode())
            if res == Protocol.FINISH:
                sock.recv(1024)
            logger.log(res, logging.INFO)

    @staticmethod
    def compile_message(operation, *params):
        body = Protocol.SEPARATOR.join(params)
        body = Protocol.SEPARATOR.join([operation.value, body])
        length = str(len(body))
        length = (10 - len(length)) * "0" + length
        return Protocol.SEPARATOR.join(["INON", length, body])

    @staticmethod
    def send_file(sock, logger, filename):
        try:
            file = open(filename, "rb").read()
        except FileNotFoundError:
            Protocol.handle_error(sock, logger, Error.FileNotFound)
            return Protocol.FINISH
        index = 0
        file_size = len(file)
        while index + Protocol.CHUNK_SIZE < file_size:
            print(index, index + Protocol.CHUNK_SIZE)
            sock.send(file[index: index + Protocol.CHUNK_SIZE])
            index += Protocol.CHUNK_SIZE
            try:
                msg = sock.recv(1024).decode()
                if msg == str(index):
                    continue
            except ConnectionResetError or ConnectionAbortedError:
                Protocol.handle_error(sock, logger, Error.ConnectionError)
                return Protocol.FINISH
        sock.send(file[index:])
        return Protocol.FINISH

    @staticmethod
    def recv_file(sock):
        file = bytearray()
        msg = sock.recv(Protocol.CHUNK_SIZE)
        i = 0
        while msg != Protocol.FINISH.encode():
            file += msg
            sock.send(f"{i}".encode())
            msg = sock.recv(Protocol.CHUNK_SIZE)
            i += Protocol.CHUNK_SIZE
        return file

    def __init__(self, path, path_users):
        self.db_manager = ThreadManager(path)
        self.auth_manager = AuthManager(path_users)

    def business_logic(self, sock, msg, logger):
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
                Protocol.handle_operation(sock, logger, OPERATIONS.WRITE, self.db_manager.write_to_thread, components)
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
