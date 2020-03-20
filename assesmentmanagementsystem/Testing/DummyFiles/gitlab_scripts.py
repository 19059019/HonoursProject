import requests
import csv
import base64
import json

GIT_SERVER = "http://0.0.0.0:30080/api/v4"
TOKEN = "6-yghasYxrvUZLZJUK8m"


def create_student(suid):
    data = {
        "email": f"{suid}@sun.ac.za",
        "password": "password",
        "username": suid,
        "name": suid,
        "skip_confirmation": "true",
        "can_create_group": "false",
    }
    resp = requests.post(
        f"{GIT_SERVER}/users", json=data, headers={"PRIVATE-TOKEN": TOKEN}
    )
    print(resp.content)
    if resp.status_code != 201:
        return "Failed operation"
    else:
        return "success"


def create_marker(suid):
    data = {
        "email": f"{suid}@sun.ac.za",
        "password": "password",
        "username": suid,
        "name": suid,
        "skip_confirmation": "true",
        "can_create_group": "true",
    }
    resp = requests.post(
        f"{GIT_SERVER}/users", json=data, headers={"PRIVATE-TOKEN": TOKEN}
    )
    if resp.status_code != 201:
        return "Failed operation"
    else:
        return "success"


def create_profiles():
    with open("../flask/web_app/resources/users.csv", "r") as users:
        users = csv.reader(users, delimiter=",")
        for user in users:
            if user[0] == "suid":
                continue
            print(f"{user[1]}: {user[0]}")
            if user[1] == "admin" or user[1] == "marker" or user[1] == "lecturer":
                create_marker(user[0])
            else:
                create_student(user[0])


def upload_file(file):
    data = {
        "id":1,
    }
    resp = requests.post(
        f"{GIT_SERVER}/projects/1/uploads",
        json=data,
        headers={"PRIVATE-TOKEN": TOKEN},
        files={"file": file},
    )

