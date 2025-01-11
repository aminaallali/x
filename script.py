import time
import subprocess
import contextlib
import os
from IPython.display import clear_output

PATH_TO_FILE = "./downloads"  # @param {type:"string"}
EMAIL = "anumwebber@gmail.com"  # Replace with your email
PASSWORD = "OutmaneHr.com12$"   # Replace with your password
FOLDER_LINK = "https://mega.nz/folder/pi1SALpD#0RJmtvr4AFxApHViU13Z6g/folder/xjFUzBDY"  # MEGA folder link

newlines = ['\n', '\r\n', '\r']

def unbuffered(proc, stream='stdout'):
    """Iterate over the process output in an unbuffered way."""
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

def list_items(folder_link):
    """
    Returns a list of (path, is_dir) for all items under `folder_link`,
    using a recursive listing via `mega-ls -R`.
    """
    cmd = ['mega-ls', '-R', folder_link]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = proc.communicate()
    
    if proc.returncode != 0:
        print("Error listing items:", stderr)
        return []
    
    """
    mega-ls -R output typically looks like:
        /Folder1
        /Folder1/FileA.txt
        /Folder2
        /Folder2/Subfolder/FileB.txt
        /FileRoot.txt

    We will parse each line to see if it represents a directory or file.
    """
    # Each line is a path that starts with '/'
    # We can identify directories vs. files with an extra 'mega-ls' call 
    # or a simple heuristic (if we see a line next with a deeper path).
    # However, for reliability, let's do a second check with 'mega-ls' on each item.
    items = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("/"):
            continue
        # Build a full mega path by appending to the folder link:
        # For example, if line="/Folder1/FileA.txt",
        # we can use "FOLDER_LINK + '/Folder1/FileA.txt'" in `mega-ls`.
        # But mega-cmd also directly allows `mega-ls "FOLDER_LINK/Folder1/FileA.txt"`.
        
        # We just store the relative path here; we’ll check is_dir next:
        items.append(line)
    
    # Now check which are directories vs. files.
    results = []
    for relative_path in items:
        # Remove leading slash
        remote_path = relative_path.lstrip("/")
        # Construct a full remote path for each item
        full_remote_path = f"{folder_link}/{remote_path}"
        
        # Check whether it's dir or file with a quick mega-ls:
        # If 'mega-ls <path>' returns an empty listing or an error, it's likely a file.
        # If it shows content, it's a folder.
        cmd_check = ['mega-ls', full_remote_path]
        proc_check = subprocess.Popen(cmd_check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out_check, err_check = proc_check.communicate()
        
        if proc_check.returncode == 0 and out_check.strip() != "":
            # It's a folder (because mega-ls returned something meaningful)
            results.append((full_remote_path, True))   # True => is_dir
        else:
            # It's a file
            results.append((full_remote_path, False))  # False => is_file

    return results

def download_item(remote_path, is_dir, local_path=PATH_TO_FILE):
    """
    Download a single file or folder from MEGA to local_path.
    """
    cmd = ['mega-get', remote_path, local_path]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    for line in unbuffered(proc):
        clear_output(wait=True)
        print(line)

def transfer():
    """
    - List all items in the remote folder (recursively).
    - Download each item individually.
    """
    items = list_items(FOLDER_LINK)
    if not items:
        print("No items found to download or an error occurred.")
        return
    
    print(f"Found {len(items)} items to download.")
    # Sort so that folders get created first — helpful if we want subfolder structure
    # But note: mega-get will create subfolders if is_dir is True, so in principle 
    # we can just download in any order. 
    # If you want to ensure folders first, you can do:
    # items.sort(key=lambda x: (not x[1], x[0]))  # Folders first
    
    for remote_path, is_dir in items:
        print(f"Downloading {'folder' if is_dir else 'file'}: {remote_path}")
        download_item(remote_path, is_dir)

try:
    login()
    transfer()
except FileNotFoundError:
    print("Could not find `mega-login` or `mega-get`. Ensure mega-cmd is installed and in PATH.")
except subprocess.CalledProcessError as e:
    print("Subprocess error:", e)
