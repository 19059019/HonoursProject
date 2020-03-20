from git_API_functions import *
from models import *
from git_handler import *
from config import *
from werkzeug import secure_filename
from tempfile import NamedTemporaryFile
from filelock import Timeout, FileLock
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
import pandas as pd
import requests
import logging
import shutil
import datetime
import tarfile
import json
import csv
import os
import re

ENV_JSON_TEMPLATE_PATH = "resources/env_template.json"
SUB_JSON_TEMPLATE_PATH = "resources/sub_template.json"
ALLOWED_EXTENSIONS = set(["zip", ".tar.bz2"])


def allowed_file(filename):
    """
    Returns if a file is allowed according to the allowed extensions
    """
    file_split = filename.rsplit(".")
    if file_split[-1] in ALLOWED_EXTENSIONS:
        return True
    elif len(file_split) > 2:
        if ".{}.{}".format(file_split[-2], file_split[-1]) in ALLOWED_EXTENSIONS:
            return True
    return False


def add_user(request_form):
    """
    Adds a user to the files
    """
    su_id = request_form["su_id"]
    title = request_form["title"]
    in_module = False
    logging.debug(request_form)
    # Add students to module list
    modules = {}
    for m in get_modules():
        if m in request_form.keys() and request_form[m] == "on":
            modules[m] = "yes"
        else:
            modules[m] = "no"
    if title == "student":
        for m in modules:
            mod_path = "resources/{}.csv".format(m)
            if m in request_form.keys() and modules[m] == "yes":
                with open(mod_path, "r") as file:
                    reader = csv.reader(file, delimiter=",")
                    in_module = False
                    for row in reader:
                        if row[0] == str(su_id):
                            in_module = True
                            break
                    if not in_module:
                        with open(mod_path, "a") as file:
                            writer = csv.writer(file)
                            writer.writerow([su_id.strip()])
    with open("resources/users.csv", "r") as file:
        reader = csv.reader(file, delimiter=",")
        headers = []
        first = False
        for row in reader:
            if not first:
                headers = row
                first = not first
            if row[0] == str(su_id):
                # TODO: Check the request to see if we are changing the user
                return
    mods = []
    for col in headers:
        if col in modules.keys():
            mods.append(modules[col])
    logging.debug(mods)
    fields = [su_id, title] + mods
    logging.debug(fields)
    with open("resources/users.csv", "a") as file:
        logging.debug(fields)
        writer = csv.writer(file)
        writer.writerow(fields)


def gen_environment_json(request_data):
    """
    This generates the environment setup file from the web app
    create submission page
    """
    # This should only be called if the environment key is on
    template = []
    with open(ENV_JSON_TEMPLATE_PATH) as json_template:
        template = json.loads(json_template.read())
    if (
        "virtual_machine_checkbox" in request_data.keys()
        and request_data["virtual_machine_checkbox"] == "on"
    ):
        template["VMProperties"]["enable"] = "true"
        template["VMProperties"]["cpus"] = request_data["cpus"]
        template["VMProperties"]["memory"] = request_data["memory"]
        if (
            "shared_folder_checkbox" in request_data.keys()
            and request_data["shared_folder_checkbox"] == "on"
        ):
            template["VMProperties"]["sharedfolder"]["include"] = "true"
            template["VMProperties"]["sharedfolder"]["path"] = request_data["file_path"]
    if "time_limit_checkbox" in request_data.keys():
        template["TestProperties"]["timeMinutes"] = request_data["time_limit"]
    if (
        "internet_restriction" in request_data.keys()
        and request_data["internet_restriction"] == "on"
    ):
        template["Firewall"]["enable"] = "true"
        if "inetkey" in request_data.keys() and request_data["inetkey"] == "on":
            template["Firewall"]["only_block_inetkey"] = "true"
        else:
            if (
                "whitelist_box" in request_data.keys()
                and request_data["whitelist_box"] == "on"
            ):
                websites = request_data["whitelist_websites"].replace(" ", "")
                template["Firewall"]["whitelist_sites"] = websites.split(",")
    return json.dumps(template)


def gen_submission_json(request_data):
    """
    This generates the submission setup file from the web app
    create submission page
    """
    template = []
    with open(SUB_JSON_TEMPLATE_PATH) as json_template:
        template = json.loads(json_template.read())
    template["Title"] = request_data["assignment_title"]
    template["module"] = request_data["module"]
    template["description"] = request_data["description"]
    template["start"] = request_data["start_date"]
    template["start_pretty"] = prettify_date(request_data["start_date"])
    template["end"] = request_data["end_date"]
    template["end_pretty"] = prettify_date(request_data["end_date"])

    if (
        "submission_checkbox" in request_data.keys()
        and request_data["submission_checkbox"] == "on"
    ):
        template["file"] = "true"
        template["file_name"] = request_data["file_path"]
    if "environment" in request_data.keys() and request_data["environment"] == "on":
        template["environment"] = "true"
    if (
        "allow_resubmissions" in request_data.keys()
        and request_data["allow_resubmissions"] == "on"
    ):
        if request_data.get("limit_resubmissions") == "on":
            template["allowed_resubmissions"] = request_data.get("resubmissions")
        else:
            template["allowed_resubmissions"] = -1
    else:
        template["allowed_resubmissions"] = 0
    if "allowed_late" in request_data.keys() and request_data["allowed_late"] == "on":
        template["allowed_late"] = "true"
    else:
        template["allowed_late"] = "false"
    if request_data.get("download_during") == "on":
        template["download_during"] = "true"
    
    return json.dumps(template)


def gen_directories(module):
    """
    This generates the directories required for a new submission
    """
    dir = "modules/{}".format(module)
    index = len([name for name in os.listdir(dir)])
    dir = "{}/{}{}".format(dir, module, index)
    os.mkdir(dir)
    os.mkdir("{}/{}".format(dir, "assignment_files"))
    os.mkdir("{}/{}".format(dir, "submissions"))
    return "{}{}".format(module, index)


def gen_assignment(request):
    """
    Calls the functions to generate the directories and assignment
    setup documents and puts them in the correct directories
    """
    request_form = request.form
    module = request_form["module"]
    ass_code = gen_directories(module)
    env_json = gen_environment_json(request_form)
    sub_json = gen_submission_json(request_form)
    sub_json = json.loads(sub_json)
    env_json = json.loads(env_json)
    sub_json["Ass_Code"] = ass_code
    if "git" in request_form.keys() and request_form["git"] == "on":
        try:
            # Add git true to the sub_json
            sub_json["git"] = "true"
            # Make call to generate the group and repositories
            gen_repositories(ass_code, request)
        except Exception as e:
            logging.error(e)
    path = "modules/{}/{}/assignment_files/".format(request_form["module"], ass_code)
    with open("{}sub.json".format(path), "w") as outfile:
        json.dump(sub_json, outfile)
    with open("{}env.json".format(path), "w") as outfile:
        json.dump(env_json, outfile)
    add_logs_file(path, ass_code)

    if sub_json["file"] == "true":
        # Check how many files
        file_count = len(request.files.getlist("submission_file"))
        # If only one file, save it
        if file_count == 1:
            path = "{}downloads".format(path)
            os.mkdir(path)
            save_file(request, path)


def save_file(request, path):
    """
    This saves the submission_file file from a post request
    to the supplied path
    """
    file = request.files["submission_file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save("{}/{}".format(path, filename))


def tar_bz2_dir(path, ass_code, name):
    """
    Create a tar.bz2 containing the directory at path and then storing it
    in the path
    """
    compressed_path = "{}/{}_{}.tar.bz2".format(path, ass_code, name)
    with tarfile.open(compressed_path, "w:bz2") as tar:
        tar.add(path, arcname=os.path.basename(path))
    return path

def get_files_path(ass_code):
    """
    Returns the path and filename of the downloads for a specific assignment
    """
    try:
        module = ass_code[:5]
        path = "modules/{}/{}/assignment_files".format(module, ass_code)

        # Check if the download is allowed at this time
        with open("{}/sub.json".format(path), "r") as sub:
            sub = json.loads(sub.read())
            if sub.get("download_during") == "true":
                start = date_html_to_python(sub["start"])
                end = date_html_to_python(sub["end"])
                if not between_dates(start, end):
                    path, filename = False, False
        if path == False:
            return filename, path
        path = "{}/downloads".format(path)
        filename = os.listdir(path)[0]
        return path, filename
    except Exception as e:
        logging.error(e)
        return False, False

def handle_submission(request, su_id):
    """
    Saves the submission if it is allowed
    """
    uuid = request.cookies.get("uuid")
    logging.debug("Cookie: {}".format(uuid))
    request_form = request.form
    logging.debug(request_form)
    ass_code = request_form["ass_code"]
    module = request_form["module_code"]
    path = "modules/{}/{}/submissions".format(module, ass_code)
    expected_file = "submission_file_{}".format(ass_code)
    if expected_file in request.files:
        file = request.files[expected_file]
        if file and allowed_file(file.filename):
            if su_id not in os.listdir(path):
                path = "{}/{}/".format(path, su_id)
                os.mkdir(path)
            else:
                path = "{}/{}/".format(path, su_id)
            if allowed_submission(su_id, ass_code):
                # Remove previous submissions
                for sub in os.listdir(path):
                    os.unlink("{}/{}".format(path, sub))
                # Add resubmission
                filename = secure_filename(file.filename)
                file.save("{}/{}".format(path, filename))
                # Log submission and date
                tempfile = NamedTemporaryFile(delete=False)
                try:
                    locks[ass_code].acquire(timeout=10)
                    with open(
                        "modules/{}/{}/assignment_files/logs.csv".format(
                            module, ass_code
                        ),
                        "rb",
                    ) as logs, tempfile:
                        logs = csv.reader(logs, delimiter=",")
                        writer = csv.writer(tempfile, delimiter=",")
                        found = False
                        for row in logs:
                            if str(row[0]) == str(su_id):
                                found = True
                                subs = int(row[2])
                                row[2] = subs + 1
                                row[3] = datetime.datetime.now()
                                row[5] = request.remote_addr
                                row[6] = uuid
                            writer.writerow(row)
                        if not found:
                            # Still log submissions if the user is not a registered user somehow
                            writer.writerow(
                                [
                                    su_id.strip(),
                                    0,
                                    1,
                                    datetime.datetime.now(),
                                    None,
                                    request.remote_addr,
                                    uuid,
                                    None,
                                    None,
                                ]
                            )
                        shutil.move(
                            tempfile.name,
                            "modules/{}/{}/assignment_files/logs.csv".format(
                                module, ass_code
                            ),
                        )
                        # Finally send email to inform student of their submission
                        send_email(su_id, ass_code)
                finally:
                    locks[ass_code].release()
            else:
                return False
        else:
            return False
    else:
        return False
    return True


def allowed_submission(su_id, ass_code):
    """
    Checks if the submission can be made
    """
    module = ass_code[:5]
    allowed_resubmissions = 0
    # Does module exist
    if not module in os.listdir("modules"):
        return False
    # Does assgnment exist
    if not ass_code in os.listdir("modules/{}".format(module)):
        return False
    else:
        # Get resubmission details
        with open(
            "modules/{}/{}/assignment_files/sub.json".format(module, ass_code), "r"
        ) as sub_json:
            data = json.loads(sub_json.read())
            allowed_resubmissions = data["allowed_resubmissions"]
    # Resubmissions set to -1 if unlimited resubs are allowed
    if allowed_resubmissions < 0:
        return assignment_allowed_submission(ass_code)
    # Has the student already made a submission
    if not su_id in os.listdir("modules/{}/{}/submissions".format(module, ass_code)):
        # Check assignment specific regulations
        allowed = assignment_allowed_submission(ass_code)
        return allowed
    elif int(made_submission_ass(su_id, ass_code)) > int(allowed_resubmissions):
        # Allow up to the resubmission number of submissions
        return False
    else:
        # Ensure that a resubmission is allowed at this point in time
        allowed = assignment_allowed_submission(ass_code)
        return allowed


def made_submission_ass(su_id, ass_code):
    """ Find the number of submissions made for an assignment for a specific student"""
    if os.path.exists(
        "modules/{}/{}/submissions/{}".format(ass_code[:5], ass_code, su_id)
    ):
        with open(
            "modules/{}/{}/assignment_files/logs.csv".format(ass_code[:5], ass_code),
            "r",
        ) as logs:
            rows = csv.reader(logs, delimiter=",")
            for row in rows:
                if str(row[0]) == (su_id):
                    logging.debug(
                        "{} has made {} subs for {}".format(su_id, row[2], ass_code)
                    )
                    return row[2]
            return 0
    else:
        return 0


def assignment_allowed_submission(ass_code):
    """
    Checks if a submission is allowed in the moment for an assignment
    """
    start = ""
    end = ""
    with open(
        "modules/{}/{}/assignment_files/sub.json".format(ass_code[:5], ass_code)
    ) as sub_json:
        template = json.loads(sub_json.read())
        allowed_late = template["allowed_late"]
        start = template["start"]
        end = template["end"]
    start = date_html_to_python(start)
    end = date_html_to_python(end)
    valid_time = between_dates(start, end)
    if not valid_time:
        if allowed_late == "true" and late_submission(end):
            logging.debug("Late submission allowed for {}".format(ass_code))
            return True
        # Return not allowed due to not falling in the allowed time frame
        logging.debug("Late submission declined for {}".format(ass_code))
        return False
    logging.debug("Assignment on time for {}".format(ass_code))
    return True


def get_subs_made(user):
    """
    returns a dictionary of all assignments with submissions made
    by the user
    """
    submissions_made = {}
    for module in user.modules:
        for ass_code in os.listdir("modules/{}".format(module)):
            if user.su_id in os.listdir(
                "modules/{}/{}/submissions".format(module, ass_code)
            ):
                submissions_made[ass_code] = "yes"
    return submissions_made


def get_resubmissions_allowed(user):
    """ Returns a dictionary of modules where resubmissions are still allowed """
    resubmissions_allowed_dict = {}
    for module in user.modules:
        for ass_code in os.listdir("modules/{}".format(module)):
            # See if resubmissions allowed for assignment
            resubmissions_allowed = 0
            submissions = 0
            with open(
                "modules/{}/{}/assignment_files/sub.json".format(module, ass_code), "r"
            ) as subs_json:
                resubmissions_allowed = json.loads(subs_json.read())[
                    "allowed_resubmissions"
                ]
            # find user submissions
            submissions = made_submission_ass(user.su_id, ass_code)
            logging.debug(
                "{} has made {} out of {} submissions for {}".format(
                    user.su_id, submissions, resubmissions_allowed, ass_code
                )
            )
            if int(submissions) > int(resubmissions_allowed):
                if resubmissions_allowed == -1:
                    resubmissions_allowed_dict[ass_code] = "true"
                else:
                    resubmissions_allowed_dict[ass_code] = "false"
                continue
            else:
                logging.debug(
                    "{} is allowed {} resubmissions".format(
                        user.su_id,
                        int(resubmissions_allowed) - int(submissions) + int(1),
                    )
                )
                resubmissions_allowed_dict[ass_code] = (
                    int(resubmissions_allowed) - int(submissions) + int(1)
                )
    return resubmissions_allowed_dict


def available_submissions(su_id):
    """
    Returns a list of all ass_codes that have available submissions
    """
    u = User(su_id)
    submissions_available = []
    for module in u.modules:
        for ass_code in os.listdir("modules/{}".format(module)):
            if allowed_submission:
                submissions_available.append(ass_code)
    return submissions_available


def date_html_to_python(html_date):
    """
    This converts the html form datetime into python format
    """
    date = html_date.split("T")[0].split("-")
    time = html_date.split("T")[1].split(":")
    return datetime.datetime(
        int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]), 0
    )


def between_dates(start, end):
    """
    See if the current time is between two dates
    """
    now = datetime.datetime.now()
    if now >= start and now <= end:
        return True
    else:
        return False


def late_submission(end):
    """
    See if the current time later than end
    """
    now = datetime.datetime.now()
    if now >= end:
        return True
    else:
        return False


def env_start(request):
    """
    Handle request for an environment to start
    """
    data = request.form
    uuid = request.cookies.get("uuid")
    ass_code = data["ass_code"]
    module = ass_code[:5]
    suid = data["suid"]
    time = data["time"]
    path = "modules/{}/{}/assignment_files/logs.csv"
    tempfile = NamedTemporaryFile(delete=False)
    logging.debug("ENV START")
    with open(path.format(module, ass_code), "rb") as logs, tempfile:
        logs = csv.reader(logs, delimiter=",")
        writer = csv.writer(tempfile, delimiter=",")
        found = False
        for row in logs:
            if row[0] == str(suid):
                found = True
                logging.debug("Col 7: " + row[7])
                if row[7] == "":
                    logging.debug("Editing File")
                    row[7] = time
            writer.writerow(row)
        if not found:
            logging.debug("Not Found")
            # Still log submissions if the user is not a registered user somehow
            writer.writerow([suid, 0, 1, None, None, None, uuid, time, None])
    shutil.move(tempfile.name, path.format(module, ass_code))


def env_end(request):
    """
    Handle request to close an environment
    """
    data = request.form
    uuid = request.cookies.get("uuid")
    ass_code = data["ass_code"]
    module = ass_code[:5]
    suid = data["suid"]
    time = data["time"]
    path = "modules/{}/{}/assignment_files/logs.csv"
    tempfile = NamedTemporaryFile(delete=False)
    logging.debug("ENV END")
    with open(path.format(module, ass_code), "rb") as logs, tempfile:
        logs = csv.reader(logs, delimiter=",")
        writer = csv.writer(tempfile, delimiter=",")
        found = False
        for row in logs:
            if row[0] == str(suid):
                found = True
                logging.debug("Col 8: " + row[8])
                if row[8] == "":
                    logging.debug("Editing File")
                    row[8] = time
            writer.writerow(row)
        if not found:
            logging.debug("Not Found")
            # Still log submissions if the user is not a registered user somehow
            writer.writerow([suid, 0, 1, None, None, None, uuid, None, time])
    shutil.move(tempfile.name, path.format(module, ass_code))


def add_logs_file(path, ass_code):
    """
    Takes submission_files path of a module and inserts the submission logfile
    """
    module = ass_code[:5]
    with open("{}logs.csv".format(path), "w") as outfile:
        outfile = csv.writer(
            outfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        outfile.writerow(
            [
                "suid",
                "commits",
                "submissions",
                "latest_submission",
                "env_id",
                "latest_ip",
                "uuid",
                "env_started",
                "env_stopped",
            ]
        )
        # Add empty log for every student
        with open("resources/{}.csv".format(module), "r") as students:
            for student in students:
                outfile.writerow(
                    [student.strip(), 0, 0, None, None, None, None, None, None]
                )
    locks[ass_code] = FileLock(
        "modules/{}/{}/assignment_files/logs.csv.lock".format(module, ass_code)
    )


def mark_assignment(request):
    """
    Instructs the marking microservice to begin marking the submissions for the specified modules
    """
    server = config["marking_server"]
    token = config["marking_token"]
    files = request.files.to_dict()
    form = request.form.to_dict()
    form["token"] = token
    logging.debug(server)
    try:
        requests.post(server, files=files, data=form, timeout=5)
    except requests.exceptions.ReadTimeout:  # this confirms you that the request has reached server
        logging.debug("Request sent")
    except Exception as e:
        logging.debug(e)
        return False
    return True


def get_modules():
    """
    Returns a list of all modules names
    """
    return pd.read_csv("./resources/modules.csv", sep=",", header=None, dtype=str)[
        0
    ].tolist()


def get_users():
    """
    Returns a list of all modules names
    """
    return pd.read_csv("./resources/users.csv", dtype=str)["suid"].tolist()


def get_lecturers():
    """
    Returns a list of all modules names
    """
    users = pd.read_csv("./resources/users.csv", dtype=str)
    return users[users["title"] == "lecturer"]["suid"].tolist()


def get_markers():
    users = pd.read_csv("./resources/users.csv", dtype=str)
    return users[users["title"] == "marker"]["suid"].tolist()


def get_students():
    users = pd.read_csv("./resources/users.csv", dtype=str)
    return users[users["title"] == "student"]["suid"].tolist()


def get_admins():
    users = pd.read_csv("./resources/users.csv", dtype=str)
    return users[users["title"] == "admin"]["suid"].tolist()


def add_module(form):
    # Add directory
    module = form["module"]
    students = form["students"]
    lecturers = form["lecturers"]
    markers = form["markers"]
    if not os.path.exists("modules/{}".format(module)):
        os.mkdir("modules/{}".format(module))
    else:
        return {"success": False}

    # add csv and students
    if not os.path.exists("resources/{}.csv".format(module)):
        with open("resources/{}.csv".format(module), "w") as outfile:
            for student in students:
                outfile.writerow([student])

    # TODO: Add git group(Do this after the varsity stuff is sorted)

    # add column to users.csv and update
    path = "./resources/users.csv"
    tempfile = NamedTemporaryFile(delete=False)
    logging.info("Adding module:" + module)
    with open(path, "rb") as users, tempfile:
        users = csv.reader(users, delimiter=",")
        writer = csv.writer(tempfile, delimiter=",")
        first = False
        for row in users:
            if first == True:
                row.append(module)
            elif row[0] in students + markers + lecturers:
                row.append("yes")
            else:
                row.append("no")
            writer.writerow(row)
    shutil.move(tempfile.name, path)


def setup_directories():
    """
    Ensure the directory system is correctly set up
    """
    if not os.path.exists("modules"):
        os.mkdir("modules")
    for module in get_modules():
        if not os.path.exists("modules/{}".format(module)):
            os.mkdir("modules/{}".format(module))
        # Lock module logs
        for ass in os.listdir("modules/{}".format(module)):
            locks[ass] = FileLock(
                "modules/{}/{}/assignment_files/logs.csv.lock".format(module, ass)
            )


def prettify_date(date):
    """
    Prettify date for display
    """
    try:
        return date_html_to_python(date).strftime("%a %d %b %Y - %H:%M")
    except:
        return date


def send_email(suid, ass_code):
    """
    Send email to confirm submission
    """
    server = config["email_server"]
    token = config["marking_token"]
    form = {"token": token, "suid": suid, "ass_code": ass_code}
    logging.debug(server)
    try:
        requests.post(server, data=form, timeout=1)
    except requests.exceptions.ReadTimeout:  # this confirms you that the request has reached server
        logging.debug("Request sent")
    except Exception as e:
        logging.debug(e)


def toggle_late_submissions(ass_code):
    """
    Allows a lecturer to toggle whether late submissions are allowed or not
    """
    try:
        module = ass_code[:5]
        path = "./modules/{}/{}/assignment_files/sub.json".format(module, ass_code)
        with open(path, "r+") as sub:
            data = json.load(sub)
            allowed_late = data["allowed_late"]
            if allowed_late == "true":
                allowed_late = "false"
            else:
                allowed_late = "true"
            data["allowed_late"] = allowed_late
            sub.seek(0)
            json.dump(data, sub, indent=4)
            sub.truncate()
        return True
    except Exception as e:
        logging.error(e)


def get_assignment_stats(ass_code):
    """
    Basic stats about an assignment
    """
    module = ass_code[:5]
    log_path = "modules/{}/{}/assignment_files/logs.csv".format(module, ass_code)
    logs = pd.read_csv(log_path)
    sub_count = len(logs[logs["submissions"] > 0])
    users = pd.read_csv("resources/users.csv")
    users = users[users[module] == "yes"]
    users = users[users["title"] == "student"]
    student_count = len(users)
    return {"students": student_count, "submissions": sub_count}

