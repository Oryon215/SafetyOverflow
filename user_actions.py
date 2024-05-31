from protocol import *
from client import Client
"""
define user logic
"""


def register_client(client: Client, username: str, password: str) -> str:
    """
    Registers a new client with the given username and password.
    :param client: The client object to send the request.
    :param username: The desired username for the new client.
    :param password: The desired password for the new client.
    :return: The server's response to the registration request.
    """
    client.send(Protocol.compile_message(OPERATIONS.REGISTER, username, password))
    return Protocol.final_value(client.recv())


def authenticate(client: Client, username: str, password: str) -> str:
    """
    Authenticates an existing client with the given username and password.
    :param client: The client object to send the request.
    :param username: The username of the client.
    :param password: The password of the client.
    :return: The server's response to the authentication request.
    """
    client.send(Protocol.compile_message(OPERATIONS.AUTH, username, password))
    return Protocol.final_value(client.recv())


def list_threads(client: Client) -> str:
    """
    Requests a list of threads from the server.
    :param client: The client object to send the request.
    :return: The server's response containing the list of threads.
    """
    client.send(Protocol.compile_message(OPERATIONS.LIST_THREADS))
    res = Protocol.final_value(client.recv())
    return res


def write_thread(client: Client, title: str, message: str, author: str, father: str, max_size ='1024') -> str:
    """
    Writes a new thread or replies to an existing thread on the server.
    :param client: The client object to send the request.
    :param title: The title of the thread.
    :param message: The content of the thread or reply.
    :param author: The author of the thread or reply.
    :param father: The parent thread ID for replies (0 for new threads).
    :return: The server's response to the write request.
    """
    client.send(Protocol.compile_message(OPERATIONS.WRITE, title, message, author, max_size, father))
    return Protocol.final_value(client.recv())


def read_thread(client: Client, title: str) -> str:
    """
    Reads a thread with the given title from the server.
    :param client: The client object to send the request.
    :param title: The title of the thread to read.
    :return: The server's response containing the thread content.
    """
    client.send(Protocol.compile_message(OPERATIONS.READ, title, '1024'))
    return Protocol.final_value(client.recv())


def download_file(client: Client, file_name: str) -> str:
    """
    Downloads a file with the given name from the server.
    :param client: The client object to send the request.
    :param file_name: The name of the file to download.
    :return: The file data received from the server.
    """
    client.send(Protocol.compile_message(OPERATIONS.DOWNLOAD_FILE, file_name))
    return Protocol.final_value(client.recv())