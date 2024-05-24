import socket
from protocol import *
import ssl

hostname = '127.0.0.1'
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations('.\\SSL\\certificate.pem')
context.check_hostname = False

class Client:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssock = context.wrap_socket(self.socket, server_hostname=hostname)
        self.logger = Logger(".\\log\\client.log", logging.INFO)

    def connect(self, ip, port):
        self.logger.log(f"Connecting to: {ip, port}.", logging.INFO)
        self.ssock.connect((ip, port))

    def send(self, msg):
        try:
            self.ssock.send(msg.encode())
        except ConnectionResetError:
            self.logger.log("Connection Reset Error.", logging.ERROR)
            self.close()

    def recv(self, size=1024, encoding="utf-8"):
        try:
            msg = self.ssock.recv(size)
            return msg.decode(encoding)
        except ConnectionResetError:
            self.ssock.close()
            self.socket.close()
            self.logger.log("Connection Reset Error.", logging.ERROR)
            return "Connection Closed."

    def close(self):
        self.logger.log("Client Closed.", logging.INFO)
        self.ssock.close()
        self.socket.close()

if __name__ == "__main__":
    c = Client()
    c.connect("127.0.0.1", 1024)
    msg = Protocol.compile_message(OPERATIONS.REGISTER, "inon", "1234")
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
    msg = Protocol.compile_message(OPERATIONS.WRITE, "New", "Hey, this is from my client.", "Client", "-1")
    c.send(msg)
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.READ, "New")
    c.send(msg)
    print(c.recv())
    msg = Protocol.compile_message(OPERATIONS.DOWNLOAD_FILE, "..\\..\\riscvemulator\\c_src\\tools\\memcheck.so")
    c.send(msg)
    print(Protocol.recv_file(c.ssock))
    msg = Protocol.compile_message(OPERATIONS.DOWNLOAD_FILE, "oh hello there")
    c.send(msg)
    print(Protocol.recv_file(c.ssock))