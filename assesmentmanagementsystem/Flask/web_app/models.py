import csv
import os
import json
import pandas as pd
import logging
import subprocess


USER_FILE = "resources/users.csv"
ASSIGNMENT_TEMPLATE = "resources/ass_template.html"


class User:
    def __init__(self, su_id):
        self.title = ""
        self.modules = []
        self.assignments = []
        self.assignments_list = []
        self.su_id = su_id
        self.get_attributes(su_id)

    def module_assignments(self, module):
        if module not in self.modules:
            return []
        else:
            return Module(module).get_assignments_list()
    
    def get_assignment(self, ass_code):
        assignment = [ass for ass in self.assignments if ass["Ass_Code"] == ass_code]
        return assignment

    def get_attributes(self, su_id):
        if su_id == None:
            return
        users = pd.read_csv("./resources/users.csv", dtype=str)
        user = users[users["suid"] == str(su_id)]
        if len(user) == 0:
            self.title = "visitor"
            return
        user = user.iloc[0]
        cols = users.columns
        self.title = user["title"]
        for i in range(2, len(cols)):
            if user[cols[i]] == "yes":
                self.modules.append(cols[i])
        for m in self.modules:
            for filename in os.listdir("modules/{}".format(m)):
                dictionary = json.loads(
                    open(
                        "modules/{}/{}/assignment_files/sub.json".format(m, filename)
                    ).read()
                )
                self.assignments.append(dictionary)
                self.assignments_list.append(filename)


class Assignment:
    def __init__(self, sub_json):
        self.sub_json = sub_json


class Module:
    def __init__(self, module):
        self.module = module
        self.users = self.get_users()

    def get_users(self):
        users = {}
        module_index = -1
        with open("resources/users.csv", "r") as user_file:
            user_file = csv.reader(user_file, delimiter=",")
            first = True
            for user in user_file:
                if first:
                    for i in range(2, len(user)):
                        if user[i] == self.module:
                            module_index = i
                            break
                    first = not first
                    continue
                else:
                    if user[module_index] == "yes":
                        users[str(user[0])] = []
        return users

    def get_students(self):
        students = []
        try:
            students = (
                pd.read_csv("resources/{}.csv".format(self.module), header=None)
                .values.flatten()
                .tolist()
            )
        except:
            logging.error("No students registered for {}".format(self.module))
        students_dict = {}
        for student in students:
            students_dict[str(student)] = []
        return students_dict

    def get_assignments_list(self):
        assignments = []
        mod_path = "modules/{}".format(self.module)
        for ass in os.listdir(mod_path):
            with open(
                "{}/{}/assignment_files/sub.json".format(mod_path, ass)
            ) as ass_file:
                assignments.append(json.load(ass_file))
        return assignments


if __name__ == "__main__":
    pass
