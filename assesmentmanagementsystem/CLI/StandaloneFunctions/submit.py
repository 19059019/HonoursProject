from login import login
import sys
import requests

URL = 'http://0.0.0.0:5000/submit'

def submit(args, session):
    if len(args) > 1:
        if not login(args[1], session):
            print("Authentication Failed. Try again.")
            return
    if len(args) > 3:
        ass_code = args[2]
        module_code = ass_code[:3]
        path = args[3]
        files = {'submission_file_{}'.format(ass_code): open(path, 'rb')}
        form = {'ass_code': ass_code, 'module_code': module_code}
        print(session.post(URL, files=files, data=form).text)



# Usage python <suid> <ass_code> <path>
if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        session = requests.Session()
        submit(args, session)
    else:
        print("Usage python <suid> <ass_code> <path>")
