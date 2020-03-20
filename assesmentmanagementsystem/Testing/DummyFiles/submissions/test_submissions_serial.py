#!/usr/bin/python3
from login import *
import requests
import logging
import sys


def submit(ass_code, path, session,id):
    """
    This attempts to submit the file at the end of the given path for the given
    assignment.
    """
    url=f"http://0.0.0.0:5000/test_submit/{id}"
    logging.info("Submiting for %s: starting", id)    
    module_code = ass_code[:5]
    files = {"submission_file_{}".format(ass_code): open(path, "rb")}
    form = {"ass_code": ass_code, "module_code": module_code}
    print(session.post(url, files=files, data=form).text)
    logging.info("Submiting for %s: finishing", id)

if __name__ == "__main__":
    users = [str(x) for x in range(int(sys.argv[1]))]
    path = "../../DummyFiles/archive.tar.bz2"
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    session = requests.Session()
    login("19059019", session)
    for user in users:
        submit("wb3723",path,  session, user)
