import socket
import threading
import time

from logger import *
import select
import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=f".\\SSL\\certificate.pem", keyfile=".\\SSL\\private_key.pem", password="yuno172")


class Server:
    """
    handle server connections
    MAX_PACE (STATIC): max user pace of packets per second
    socket: socket connection
    ssock: secure socket connection
    business_logic: server business logic
    logger: logger object
    """
    MAX_PACE = 8

    def __init__(self, ip: str, port: int, business_logic, timeout: float = 1.0) -> None:
        """
        Constructor
        :param ip: internet protocol address
        :param port: port number
        :param business_logic: server business logic function
        :param timeout: socket timeout (optional)
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.socket.settimeout(timeout)
        self.ssock = context.wrap_socket(self.socket, server_side=True)
        self.business_logic = business_logic
        self.logger = Logger(".\\log\\server.log")
        self.logger.log(f"Server set up at {ip, port}.", logging.INFO)

    def handle_client(self, sock: ssl.SSLSocket) -> None:
        """
        handle one client thread
        :param sock: client socket
        :return: None
        """
        start = time.time()
        packets = 0
        while True:
            current = time.time()
            if current - start == 0:
                continue
            if current - start > 1:
                start = current
                packets = 0
            if packets > Server.MAX_PACE:  # prevent DDOS
                sock.close()
                break
            try:
                msg = sock.recv(1024).decode()
                if msg == '':
                    sock.close()
                    break
                self.business_logic(sock, msg, self.logger)
                packets += 1
            except ConnectionResetError:
                sock.close()
                self.logger.log("Connection Reset Error", logging.ERROR)
                break

    def accept(self) -> None:
        """
        run server
        :return: None
        """
        while True:
            self.ssock.listen(1)
            rlist, wlist, xlist = select.select([self.ssock], [], [], 0)
            if len(rlist) > 0:
                user_sock, addr = self.ssock.accept()
                self.logger.log(f"Connection accepted from {addr}.", logging.INFO)
                thread = threading.Thread(target=self.handle_client, args=(user_sock, ))
                thread.start()

    def close(self) -> None:
        """
        close server socket
        :return: None
        """
        self.logger.log("Server Closed.", logging.INFO)
        self.ssock.close()
        self.socket.close()


def business_logic(sock, msg, logger):
    print(msg)
    sock.send(msg.encode())


if __name__ == "__main__":
    s = Server("127.0.0.1", 1025, business_logic)
    try:
        s.accept()
    except KeyboardInterrupt:
        s.close()

