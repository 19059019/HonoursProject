from login import login
import sys
import requests

# Takes assignment code as argument
URL = "http://0.0.0.0:5000/download_submissions/{}"

def download_submission_files(session, ass_code):
    r = session.get(URL.format(ass_code)) 
    with open('{}_submissions.tar.bz2'.format(ass_code), 'wb') as f:
        f.write(r.content)

# Usage python <suid> <ass_code>
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 3:
        session = requests.Session()
        login(args[1], session)
        download_submission_files(session, args[2])