from flask import *
from client import *
from user_actions import *

WHITE_LIST = ['_', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
for i in range(ord('a'), ord('z') + 1):
    WHITE_LIST.append(chr(i))
CLIENT = Client()
FILE_LIST = ["c_src\\tools\\memcheck.so", "cpu.o"]
USERS_LOGGED = []


def check_users():
    return request.cookies.get("name") in USERS_LOGGED


def white_list(string):
    if string is not None:
        for ch in string:
            if ch not in WHITE_LIST:
                return False
    return True


def error(error_msg, file):
    return render_template(f'{file}', error_message=error_msg)


app = Flask(__name__)
app.static_folder = 'static'


@app.route('/', methods=["GET", "POST"])
def home():
    if not white_list(request.form.get("pwd")) or not white_list(request.form.get("username")):
        error_message = "Password and username must contain only characters, numbers, and underscore."
        return error(error_message, 'home.html')
    if request.method == "POST":
        logged_message = authenticate(CLIENT, request.form.get("username"), request.form.get("pwd"))
        if "incorrect" in logged_message:
            return error(logged_message, 'home.html')
        USERS_LOGGED.append(request.form.get("username"))
        resp = make_response(render_template('home.html', logged_message=logged_message))
        resp.set_cookie("name", request.form.get("username"))
        return resp
    return render_template('home.html')


@app.route('/register.html', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form.get("username") == '' or request.form.get("pwd") == '':
            error_message = "Password and Username must include at least 1 character."
            return error(error_message, 'register.html')
        if not white_list(request.form.get("pwd")) or not white_list(request.form.get("username")):
            error_message = "Password and username must contain only characters, numbers, and underscore."
            return error(error_message, 'register.html')
        if request.form.get("pwd") != request.form.get("pwd2"):
            error_message = "Passwords don't match."
            return error(error_message, 'register.html')
        success_message = register_client(CLIENT, request.form.get("username"), request.form.get("pwd"))
        if success_message == f"User {request.form.get('username')} Successfully added":
            return render_template('register.html', success_message=success_message)
        return error(success_message, 'register.html')
    return render_template('register.html')


@app.route('/forum.html', methods=["GET", "POST"])
def forum():
    if not check_users():
        return "Error user not connected."
    if request.form.get('new-thread') is not None:
        if white_list(request.form.get('new-thread')):
            write_thread(CLIENT, request.form.get('new-thread'), request.form.get('first-comment'),
                     request.cookies.get("name"), str(-1))
    thread = request.args.get('thread')
    if thread is None:
        threads = list_threads(CLIENT)
        if threads == 'Threads:\n\t':
            return render_template('forum.html', threads=[], headline='No Threads available currently.')
        parts = threads.split(":")
        return render_template('forum.html', threads=":".join(parts[1:]).split(".")[:-1], headline=parts[0])
    else:
        thread = "".join(thread.split("(Published")[:-1])
        thread = "".join([c for c in thread if c != "\n" and c != "\t"])[:-1]
        if request.method == "POST":
            write_thread(CLIENT, thread, request.form.get("new-comment"), request.cookies.get("name"), str(-1))
        res = read_thread(CLIENT, thread)
        print(res)
        return render_template('forum.html', comments=res)


@app.route('/download.html', methods=["GET", "POST"])
def download():
    if not check_users():
        return "Error user not connected."
    if request.method == "POST":
        filename = request.form.get("files")
        if not os.path.exists(f".\\files\\{filename}"):
            bytes = download_file(CLIENT, f"C:\\Users\\User\\RiscVEmulator\\{filename}")
            with open(f".\\files\\{filename}", 'wb') as f:
                f.write(bytes)
        return send_file(f".\\files\\{filename}", as_attachment=True)
    return render_template('download.html', filenames=FILE_LIST)


if __name__ == '__main__':
    CLIENT.connect("127.0.0.1", 1024)
    app.run(port=8080)
