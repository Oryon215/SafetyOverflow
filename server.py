import socket
import threading
from logger import *
import select
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=f".\\SSL\\certificate.pem", keyfile=".\\SSL\\private_key.pem", password="yuno172")

class Server:
    def __init__(self, ip, port, business_logic, timeout=1.0):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.socket.settimeout(timeout)
        self.ssock = context.wrap_socket(self.socket, server_side=True)
        self.business_logic = business_logic
        self.logger = Logger(".\\log\\server.log")
        self.logger.log(f"Server set up at {ip, port}.", logging.INFO)

    def handle_client(self, sock):
        while True:
            try:
                msg = sock.recv(1024).decode()
                if msg == '':
                    sock.close()
                    break
                self.business_logic(sock, msg, self.logger)
            except ConnectionResetError:
                sock.close()
                self.logger.log("Connection Reset Error", logging.ERROR)
                break

    def accept(self):
        while True:
            self.ssock.listen(1)
            rlist, wlist, xlist = select.select([self.ssock], [], [], 0)
            if len(rlist) > 0:
                user_sock, addr = self.ssock.accept()
                self.logger.log(f"Connection accepted from {addr}.", logging.INFO)
                thread = threading.Thread(target=self.handle_client, args=(user_sock, ))
                thread.start()

    def close(self):
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

