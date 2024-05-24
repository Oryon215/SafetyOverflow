from protocol import *


def register_client(client, username, password):
    client.send(Protocol.compile_message(OPERATIONS.REGISTER, username, password))
    return client.recv()


def authenticate(client, username, password):
    client.send(Protocol.compile_message(OPERATIONS.AUTH, username, password))
    return client.recv()


def list_threads(client):
    client.send(Protocol.compile_message(OPERATIONS.LIST_THREADS))
    return client.recv()


def write_thread(client, title, message, author, father):
    client.send(Protocol.compile_message(OPERATIONS.WRITE, title, message, author, father))
    return client.recv()


def read_thread(client, title):
    client.send(Protocol.compile_message(OPERATIONS.READ, title))
    return client.recv()


def download_file(client, file_name):
    client.send(Protocol.compile_message(OPERATIONS.DOWNLOAD_FILE, file_name))
    return Protocol.recv_file(client.ssock)
