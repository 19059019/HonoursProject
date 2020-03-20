from login import login
import sys
import requests

URL = "http://0.0.0.0:5000/create_assignment_cli"


def download_files(session):
    r = session.get(URL)
    with open("downloaded.tar.bz2", "wb") as f:
        f.write(r.content)


def create_sub(session, sub, env=None):
    if env != None:
        files = {"sub.json": open(sub, "rb"), "env.json": open(env, "rb")}
    else:
        files = {"sub.json": open(sub, "rb")}
    print(session.post(URL, files=files).text)


# Usage python <suid> [sub.json path] [env.json path]
if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        session = requests.Session()
        login(args[1], session)
        if len(args) == 2:
            download_files(session)
        elif len(args) == 3:
            create_sub(session, args[2])
        elif len(args) == 4:
            create_sub(session, args[2], args[3])
    else:
        print("Usage: python <suid> [sub.json path] [env.json path]")

