import socket
import ssl
import logging
from logger import Logger
hostname = '127.0.0.1'
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations('.\\SSL\\certificate.pem')
context.check_hostname = False


class Client:
    """
    manage client connection
    socket (Socket): socket connection object
    ssock (SSLSocket): secure socket connection
    logger (Logger): logger object
    """
    def __init__(self) -> None:
        """
        Constructor
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssock = context.wrap_socket(self.socket, server_hostname=hostname)
        self.logger = Logger(".\\log\\client.log")

    def connect(self, ip: str, port: int) -> None:
        """
        Connect to server
        :param ip: ip
        :param port: port
        :return: None
        """
        try:
            self.logger.log(f"Connecting to: {ip, port}.", logging.INFO)
            self.ssock.connect((ip, port))
        except ConnectionRefusedError:
            exit(0)

    def send(self, msg: str) -> None:
        """
        send message to server
        :param msg: packet content
        :return: None
        """
        try:
            self.ssock.send(msg.encode())
        except ssl.SSLEOFError:
            self.logger.log("Connection Reset Error.", logging.ERROR)
            self.close()

    def recv(self, size: int = 1024, encoding="utf-8"):
        """
        receive message from server
        :param size: message size
        :param encoding: packet encoding
        :return: server message decoded
        """
        try:
            msg = self.ssock.recv(size)
            return msg.decode(encoding)
        except Exception as e:
            self.logger.log(e, logging.ERROR)
            self.close()
            return "Connection Closed."

    def close(self) -> None:
        """
        close client socket
        :return: None
        """
        self.logger.log("Client Closed.", logging.INFO)
        self.ssock.close()
        self.socket.close()
        raise ConnectionAbortedError


def tests():
    from protocol import OPERATIONS, Protocol
    c = Client()
    c.connect("127.0.0.1", 1024)
    msg = Protocol.compile_message(OPERATIONS.REGISTER, "inon", "1234")
    print("sent")
    c.send(msg)
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.AUTH, "inon", "1234")
    c.send(msg)
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.AUTH, "inon", "1235")
    c.send(msg)
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.LIST_THREADS)
    c.send(msg)
    print("waiting...")
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.WRITE, "New", "Hey, this is from my client.", "Client", '1024', '-1')
    c.send(msg)
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.READ, "New", '1024')
    c.send(msg)
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.DOWNLOAD_FILE, ".\\files\\cpu.o")
    c.send(msg)
    print(Protocol.recv_file(c.ssock))


def main():
    from server import Server
    import time

    t0 = time.time()
    c = Client()
    c.connect('127.0.0.1', 1024)
    t1 = time.time()
    for j in range(10):
        t0 = time.time()
        for i in range(Server.MAX_PACE):
            print("in")
            c.send('10')
        print("sleeping...")
        time.sleep(1.1 - (time.time() - t0))


if __name__ == "__main__":
    main()
