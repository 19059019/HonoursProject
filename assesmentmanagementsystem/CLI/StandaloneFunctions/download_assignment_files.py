from login import login
from lxml import html
import sys
import requests

# Takes assignment code as argument
URL = "http://0.0.0.0:5000/download_ass_files/{}"

def download_files(session, ass_code):
    r = session.get(URL.format(ass_code)) 
    with open('{}_downloads.tar.bz2'.format(ass_code), 'wb') as f:
        f.write(r.content)

# Usage python <suid> <ass_code>
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 3:
        session = requests.Session()
        login(args, session)
        download_files(session, args[2])