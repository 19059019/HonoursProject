#!/usr/bin/env python
from login import login
import sys
import requests
import numpy as np
import time

URL = "https://hermes.cs.sun.ac.za/modules/manage"


def add_students_from_file(args, session):
    if len(args) > 1:
        if not login(args[1], session):
            print("Authentication Failed. Try again.")
            return
    if len(args) > 3:
        module = args[2]
        path = args[3]
        students = np.genfromtxt(path).astype(int).astype(str)
        print(module)
        form = {module: "on", "title": "student", "su_id": " "}
        for su_id in students:
            form["su_id"] = su_id
            resp = session.post(URL, data=form)
            print(form)
            print(resp.status_code)


# Usage python <suid> <module> <student file path>
if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        session = requests.Session()
        add_students_from_file(args, session)
    else:
        print("Usage python <suid> <module> <student file path>")
