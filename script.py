import time
import subprocess
import contextlib
from IPython.display import clear_output

PATH_TO_FILE = "./downloads"  # @param {type:"string"}
EMAIL = "anumwebber@gmail.com"  # Replace with your email
PASSWORD = "OutmaneHr.com12$"        # Replace with your password
FILE_LINK = "https://mega.nz/folder/pi1SALpD#0RJmtvr4AFxApHViU13Z6g/folder/xjFUzBDY"  # Add your MEGA file link here

newlines = ['\n', '\r\n', '\r']

def unbuffered(proc, stream='stdout'):
    stream = getattr(proc, stream)
    with contextlib.closing(stream):
        while True:
            out = []
            last = stream.read(1)
            if last == '' and proc.poll() is not None:
                break
            while last not in newlines:
                if last == '' and proc.poll() is not None:
                    break
                out.append(last)
                last = stream.read(1)
            out = ''.join(out)
            yield out

def logout():
    cmd = ['mega-logout']
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Failed to logout existing MEGA session.")

def login():
    logout()  # Ensure no existing sessions
    cmd = ['mega-login', EMAIL, PASSWORD]
    subprocess.run(cmd, check=True)

def transfare():
    cmd = ['mega-get', FILE_LINK, PATH_TO_FILE]  # Use FILE_LINK instead of remote path
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    for line in unbuffered(proc):
        clear_output(wait=True)
        print(line)

try:
    login()
    transfare()
except FileNotFoundError:
    print("Login your account!")
