from models import *
from git_API_functions import *
from config import *
from werkzeug import secure_filename
from yaml import safe_load, safe_dump
from tempfile import NamedTemporaryFile
from datetime import datetime
import pandas as pd
import json
import logging
import shutil
import csv
import time

def handle_git_push(data):
    """ Log a commit if the student exists """
    su_id = data["user_username"].encode("utf-8")
    ass_code = data["project"]["namespace"].encode("utf-8")
    module = ass_code[:5]
    path = "modules/{}/{}/assignment_files/logs.csv"
    commits = 0
    logging.info("Git hook: {} {} {}".format(module, ass_code, su_id))
    if module not in os.listdir("modules") or su_id == "root" or su_id == "19059019":
        return
    tempfile = NamedTemporaryFile(delete=False)
    try:
        locks[ass_code].acquire(timeout=10)
        with open(path.format(module, ass_code), "rb") as logs, tempfile:
            logging.info("{} Pushing for {}".format(su_id, ass_code))
            logs = csv.reader(logs, delimiter=",")
            writer = csv.writer(tempfile, delimiter=",")
            for row in logs:
                if row[0] == su_id:
                    commits = int(row[1])
                    row[1] = commits + 1
                    row[3] = datetime.now()
                writer.writerow(row)
        shutil.move(tempfile.name, path.format(module, ass_code))
    finally:
        locks[ass_code].release()


def gen_repositories(ass_code, request):
    """ Create repositories for an assignment"""
    logging.info("Making repositories for {}/{}".format(ass_code[:5], ass_code))
    request_form = request.form
    module = request_form["module"]
    parent = False
    modules = pd.read_csv("./resources/modules.csv", header=None)
    try:
        parent = int(modules[modules[0] == module][1])
    except Exception as e:
        parent = False
        logging.error(e)
    if parent:
        try:
            # Gen subgroup with asscode
            logging.info("Creating group {} with parent_id {}".format(ass_code, parent))
            group = gl.groups.create(
                {"name": ass_code, "path": ass_code, "parent_id": parent}
            )
            # Ensure that all markers and lecturers have reporter access to the group
            users = pd.read_csv("./resources/users.csv")
            users = users[users[module] == "yes"]
            priv_users = users[users["title"] != "student"]["suid"].tolist()
            for user in priv_users:
                try:
                    git_user = gl.users.list(username=user)[0]
                    group.members.create(
                        {
                            "user_id": git_user.id,
                            "access_level": gitlab.REPORTER_ACCESS,
                        }
                    )
                except Exception as e:
                    logging.error(e)
            if (
                "test_file" in request.files.keys()
                and "requirements" in request.files.keys()
                and request.files["test_file"]
                and request.files["requirements"]
            ):
                req_file = request.files["requirements"]
                test_file = request.files["test_file"]
                test_file_name = secure_filename(request.files["test_file"].filename)
                file_path = "modules/{}/{}/assignment_files/".format(module, ass_code)
                # Save the CI files
                test_file.save("{}{}".format(file_path, test_file_name))
                req_file.save("{}{}".format(file_path, "requirements.txt"))
            # Gen repositories for each student in that subgroup with developer access
            with open("resources/{}.csv".format(module), "r") as users:
                users = csv.reader(users, delimiter=",")
                for user in users:
                    # Create project
                    logging.debug("Creating project: {}_{}".format(ass_code, user[0]))
                    project = gl.projects.create(
                        {
                            "name": "{}_{}".format(ass_code, user[0]),
                            "namespace_id": group.id,
                            "initialize_with_readme": "true",
                            "shared_runners_enabled": "true",
                            "jobs_enabled": "true",
                        }
                    )
                    # Add webhook to catch commits
                    logging.debug("hook url: {}".format(config["server"]))
                    project.hooks.create(
                        {
                            "url": "{}/git-push".format(config["server"]),
                            "push_events": "true",
                        }
                    )
                    logging.debug("Created hook")
                    # Get user
                    user = gl.users.list(username=user)[0]
                    # Add user as a developer to the project
                    project.members.create(
                        {"user_id": user.id, "access_level": gitlab.MAINTAINER_ACCESS}
                    )
                    logging.debug("added user to project")
                    ci_file = []
                    if (
                        "ci_test" in request_form.keys()
                        and request_form["ci_test"] == "on"
                        or "stylechecker" in request_form.keys()
                        and request_form["stylechecker"] == "on"
                    ):
                        with open("resources/ci_template.yml", "r") as template:
                            ci_file = safe_load(template)
                            logging.debug("CI template open here")
                            if request_form.get("ci_test") == "on":
                                logging.debug("CI Tests")
                                # CI Files (gitlab-ci.yml, requirements.txt, testfile.py)
                                if (
                                    request.files["test_file"]
                                    and request.files["requirements"]
                                ):
                                    logging.debug("Files in form")
                                    # Requirements file
                                    with open(
                                        "{}requirements.txt".format(file_path), "r"
                                    ) as req:
                                        f = project.files.create(
                                            {
                                                "file_path": "requirements.txt",
                                                "branch": "master",
                                                "content": req.read(),
                                                "author_email": "root@root.co.za",
                                                "author_name": "root",
                                                "commit_message": "Added Requirements file",
                                            }
                                        )
                                        logging.debug("Added requirements")
                                    # Test file
                                    with open(
                                        "{}{}".format(file_path, test_file_name), "r"
                                    ) as test:
                                        f = project.files.create(
                                            {
                                                "file_path": test_file_name,
                                                "branch": "master",
                                                "content": test.read(),
                                                "author_email": "root@root.co.za",
                                                "author_name": "root",
                                                "commit_message": "Added testing file",
                                            }
                                        )
                                        logging.debug("Added test file")
                                    # edit yaml
                                    ci_file["test"]["script"].append(
                                        "python {}".format(test_file_name)
                                    )
                            else:
                                logging.debug("Other side of the else")
                                index = ci_file["stages"].index("test") 
                                del ci_file["stages"][index]
                                del ci_file["test"]
                            logging.debug("Customising yaml")
                            # Customise CI yaml file
                            ci_file["image"] = request_form["py_version"]
                            if request_form.get("stylechecker") != "on":
                                index = ci_file["stages"].index("style") 
                                del ci_file["stages"][index]
                                del ci_file["style"]
                            logging.debug("Inserting ci config file")
                            # add .gitlab-ci.yml
                            project.files.create(
                                {
                                    "file_path": ".gitlab-ci.yml",
                                    "branch": "master",
                                    "content": safe_dump(ci_file),
                                    "author_email": "root@root.co.za",
                                    "author_name": "root",
                                    "commit_message": "Added CI file",
                                }
                            )
        except Exception as e:
            logging.error(e)
    else:
        logging.error("Issue creating git subgroup")
