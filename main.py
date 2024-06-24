from flask import *
from client import *
from user_actions import *
from random import randint
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
"""
Manage Website
"""

app = Flask(__name__)  # flask website object
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)  # flask transportation limiter
BLACK_LIST = ['\"', "\n"]  # limit user input
# for i in range(ord('a'), ord('z') + 1):
#     WHITE_LIST.append(chr(i))
CLIENT = Client()  # for communication with server
FILE_LIST = ["memcheck.so", "cpu.o", 'null.so']  # files for downloading
USERS_LOGGED = []  # currently logged users
tokens = {}  # csrf tokens


def aborted_error(function):
    """
    wrapper function for error server aborted
    :param function: website function
    :return: wrapped function
    """
    def wrapper():
        try:
            return function()
        except ConnectionAbortedError:
            return "Error. Server disconnected. Try to login later!"
    wrapper.__name__ = function.__name__
    return wrapper


def check_users() -> bool:
    # return true if user is currently logged in otherwise false
    return request.cookies.get("name") in USERS_LOGGED


def white_list(string: str) -> bool:
    # :param: string - general input
    # return False if string input is in black list to prevent injection attacks otherwise True
    if string is not None:
        for ch in string:
            if ch in BLACK_LIST:
                return False
    return True


def error(error_msg: str, file: str) -> str:
    """
    handle error in html file
    :param error_msg: error message
    :param file: html template
    :return: return error template of page with error message
    """
    res = render_template(f'{file}', error_message=error_msg)
    return res

app = Flask(__name__)
app.static_folder = 'static'


@app.route('/', methods=["GET", "POST"])
@aborted_error
def home() -> str or Response:
    # render home screen of website
    # check login request (POST)
    if request.method == "POST":
        # check valid input (in white list)
        if not white_list(request.form.get("pwd")) or not white_list(request.form.get("username")):
            error_message = "Password and username mustn't contain quotation marks or newline."
            return error(error_message, 'home.html')

        # send server authentication information
        logged_message = authenticate(CLIENT, request.form.get("username"), request.form.get("pwd"))
        if "incorrect" in logged_message:  # in case of wrong information
            return error(logged_message, 'home.html')
        # otherwise log user
        USERS_LOGGED.append(request.form.get("username"))
        resp = make_response(render_template('home.html', logged_message=logged_message))
        resp.set_cookie("name", request.form.get("username"))
        return resp
    # if user has already logged in (GET)
    if request.cookies.get("name") in USERS_LOGGED:
        return make_response(render_template('home.html', logged_message=f"Welcome {request.cookies.get("name")}"))
    # default
    return render_template('home.html')


@app.route('/register.html', methods=["GET", "POST"])
@aborted_error
def register() -> str:
    # register request (POST)
    if request.method == "POST":
        # check input length validity
        if request.form.get("username") == '' or request.form.get("pwd") == '':
            error_message = "Password and Username must include at least 1 character."
            return error(error_message, 'register.html')
        # check input validity (SQL Injection)
        if not white_list(request.form.get("pwd")) or not white_list(request.form.get("username")):
            error_message = "Password and username mustn't contain quotation marks or newline."
            return error(error_message, 'register.html')
        # check password authentication validity
        if request.form.get("pwd") != request.form.get("pwd2"):
            error_message = "Passwords don't match."
            return error(error_message, 'register.html')
        # send server registration request
        success_message = register_client(CLIENT, request.form.get("username"), request.form.get("pwd"))
        # return server response
        if success_message == f"User {request.form.get('username')} Successfully added":
            return render_template('register.html', success_message=success_message)
        return error(success_message, 'register.html')
    # default page (GET)
    return render_template('register.html')


@app.route('/forum.html', methods=["GET", "POST"])
@aborted_error
def forum() -> str:
    """
    render forum template
    :return: rendered version of forum template
    """
    error = None
    if request.method == "POST" and request.form.get("csrf") != tokens.get(request.cookies.get("name")):
        return f"{tokens.get(request.cookies.get("name"))}, {request.form.get("csrf")}"
    csrf_token = str(hash(randint(0, 10 ** 10)))
    tokens[request.cookies.get("name")] = csrf_token
    # check if user has permission to enter
    if not check_users():
        return "Error user not connected."
    # check for new thread request (POST)
    if request.form.get('new-thread') is not None:
        if white_list(request.form.get('new-thread')):
            res = create_thread(CLIENT, request.form.get("new-thread"))
            if res == "Thread Name already exists.":
                error = res
            else:
                write_thread(CLIENT, request.form.get('new-thread'), request.form.get('first-comment'),
                             request.cookies.get("name"), str(-1), '1024')
    thread = request.args.get('thread')
    # check for default request
    if thread is None:
        threads = list_threads(CLIENT)
        if threads == 'Threads:\n\t':
            return render_template('forum.html', threads=[], headline='No Threads available currently.', csrf=csrf_token)
        print(threads)
        parts = threads.split(":")
        return render_template('forum.html', threads=":".join(parts[1:]).split(".")[:-1], headline=parts[0], csrf=csrf_token, error_message=error)
    # check for thread view request (GET)
    thread = "".join(thread.split("(Published")[:-1])
    thread = "".join([c for c in thread if c != "\n" and c != "\t"])[:-1]
    # check for comment writing request (POST)
    if request.method == "POST":
        write_thread(CLIENT, thread, request.form.get("new-comment"), request.cookies.get("name"), str(-1))
    res = read_thread(CLIENT, thread)
    return render_template('forum.html', comments=res, csrf=csrf_token)


@app.route('/download.html', methods=["GET", "POST"])
@aborted_error
def download() -> str or Response:
    """
    render download template
    :return: rendered download template
    """
    # check if user has permission to enter
    if not check_users():
        return "Error user not connected."
    if request.method == "POST":
        # check for download request (POST)
        filename = request.form.get("files")
        print(filename)
        if filename in FILE_LIST:
            if not os.path.exists(f".\\user_files\\{filename}"):
                res = download_file(CLIENT, filename)
                with open(f".\\user_files\\{filename}", 'wb') as file:
                    file.write(res)
                    file.close()
            return send_file(f".\\user_files\\{filename}", as_attachment=True)
    # default page (GET)
    return render_template('download.html', filenames=FILE_LIST)


if __name__ == '__main__':
    CLIENT.connect("127.0.0.1", 1024)
    if not os.path.exists(f".\\user_files"):
        os.mkdir("user_files")
    app.run()
    os.remove("user_files")