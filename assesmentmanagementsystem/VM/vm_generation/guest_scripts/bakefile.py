#!/usr/bin/python3
import os
import sqlite3
import pwd
import json
import socket
from datetime import datetime

time = datetime.now()
time = datetime.timestamp(time)
exp = datetime(2020, 5, 17)
exp = datetime.timestamp(exp)
expires = "July 30, 2020 12:50PM"
_cookieName = "uuid"
host_key = str(socket.gethostbyname(socket.gethostname()))


def run_query():
    db = "/home/19059019/.config/google-chrome/Default/Cookies"
    # db = "/home/michael/.config/google-chrome/Default/Cookies"
    if os.path.isfile(db):
        print("wololo")
        connection = sqlite3.connect(db)
        querier = connection.cursor()

        cookies = querier.execute("SELECT * FROM cookies where host_key='0.0.0.0';")
        # cookies = querier.execute("DELETE FROM cookies where name='uuid';")
        # cookies = querier.execute("SELECT * FROM sqlite_master;")
        for cookie in cookies:
            print(cookie)
        # for s in schema:
        #     print("##########################")
        #     for a in s:
        #         print(a)
        #     print("##########################")
        # params = (
        #     13208962634052730,
        #     host_key,
        #     "uuid",
        #     "",
        #     "/",
        #     13217609849093807,
        #     0,
        #     0,
        #     13208962649093807,
        #     1,
        #     1,
        #     1,
        #     b'v11\x08\xcb\x9f\xe6\x9c\xcb"\xc3\xad:rf\xe7q\xbf\x04',
        #     0,
        # )
        # print(params)
        # print(
        #     querier.execute(
        #         "INSERT INTO cookies (creation_utc, host_key, name, value, path, expires_utc, is_secure, is_httponly, last_access_utc, has_expires, is_persistent, priority, encrypted_value, firstpartyonly)\
        #          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?)",
        #         params,
        #     )
        # )
        connection.commit()


if __name__ == "__main__":
    run_query()
    pass
