from server import *
from protocol import *
IP = "127.0.0.1"
PORT = 1024


def main_server():
    p = Protocol("database\\", ".\\users")
    s = Server(IP, PORT, p.business_logic)
    try:
        s.accept()
    except KeyboardInterrupt:
        s.close()


if __name__ == "__main__":
    main_server()
