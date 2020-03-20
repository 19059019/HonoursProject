import config
import logging
import os
import shutil
import tarfile
import zipfile
from werkzeug import secure_filename
from shutil import copyfile
from datetime import datetime

SETUP = "Setting up"
EXTRACTING = "Extracting submissions"
MARK = "Marking"
DONE = "Marking complete"
ALLOWED_EXTENSIONS = set(["zip", ".tar.bz2"])


def verify_token(request):
    """
    Ensure that the token valid
    """
    if request.form.get("token") in config.tokens.values():
        return True
    return False


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


def extract(file_path, dest_path):
    """
    Extract if its a tar.bz2 or zip file
    """
    if not allowed_file(file_path):
        return
    elif file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(dest_path)
    elif file_path.endswith(".tar.bz2"):
        with tarfile.open(file_path, "r:bz2") as tar:
            tar.extractall(dest_path)

def mark_assignment(request):
    status = SETUP
    now = datetime.now()
    now = now.strftime("%d%m%H%M")
    ass_code = request.form.get("ass_code")
    module = ass_code[:5]
    # Get marking script
    files = request.files.to_dict()
    if "requirements" not in files or "marking_script" not in files:
        return {"status": f"Incorrect marking files, {ass_code}"}

    # Extract all submissions into assignment directory
    try:
        os.mkdir("tmp")
    except:
        logging.debug("tmp already exists")
    try:
        os.mkdir("logs")
    except:
        logging.debug("logs already exists")


    dest_path = f"tmp/{ass_code}"
    logs_path = f"logs/{ass_code}_logs_{now}"
    src_path = f"../web_app/modules/{module}/{ass_code}/submissions"
    if os.path.isdir(logs_path): shutil.rmtree(logs_path)
    os.mkdir(logs_path)
    os.mkdir(dest_path)
    os.mkdir(f"{dest_path}/submissions")
    if not save_file(files["requirements"], dest_path, "requirements"):
        marking_teardown(ass_code)
        return {"status": f"Error with requirements, {ass_code}"}
    os.system(f"cp resources/mark.sh tmp/{ass_code}")
    status = EXTRACTING
    if not save_file(files["marking_script"], dest_path, "marking_script"):
        marking_teardown(ass_code)
        return {"status": f"Error with marking script, {ass_code}"}
    for dir in os.listdir(src_path):
        os.mkdir(f"{dest_path}/submissions/{dir}")
        for filename in os.listdir(f"{src_path}/{dir}"):
            src = f"{src_path}/{dir}/{filename}"
            dst = f"{dest_path}/submissions/{dir}"
            extract(src, dst)
            #Check if the extracted was just a directory
            extracted = os.listdir(dst)
            if len(extracted) == 1 and os.path.isdir(f"{dst}/{extracted[0]}"):
                for f in os.listdir(f"{dst}/{extracted[0]}"):
                    shutil.move(f"{dst}/{extracted[0]}/{f}", dst)
            # put the marking script in each directory
            copyfile(f"{dest_path}/marking.py", f"{dst}/marking.py")

    logging.info("Creating Dockerfile")
    # Create docker file from submission details
    lang_line = f"FROM {request.form.get('language')}"
    copy_line = f"COPY tmp/{ass_code} /app"
    workdir_line = "WORKDIR /app"
    env_line = 'ENV PYTHONPATH "${PYTHONPATH}:/app"'
    run_line = "RUN pip install -r requirements.txt"
    cmd_line = "CMD ./mark.sh"
    lines = [
        lang_line,
        copy_line,
        workdir_line,
        env_line,
        run_line,
        cmd_line,
    ]
    with open(f"Dockerfile", "w+") as dockerfile:
        for line in lines:
            dockerfile.write(f"{line}\n")
    # start self desctructing docker container that runs the marking scripts
    os.system(f"sudo docker build --tag {ass_code} .")
    os.system(f'sudo docker run --rm -it -v "$(pwd)"/{logs_path}:/app/logs {ass_code}')

    # Remove root only access to log files
    uid, gid = os.stat(os.getcwd()).st_uid, os.stat(os.getcwd()).st_gid
    os.chown("logs", uid, gid)
    os.chown(logs_path, uid, gid)
    for dir in os.listdir(logs_path):
        os.chown(f"{logs_path}/{dir}", uid, gid)

    marking_teardown(ass_code)
    
    return {"status": f"{status} {ass_code}"}

def marking_teardown(ass_code):
    """
    Remove temporary marking files
    """
    try:
        if os.path.isdir(("tmp")):
            if len(os.listdir()) == 1:
                shutil.rmtree("tmp")
            else:
                shutil.rmtree(f"tmp/{ass_code}")
        os.system("rm Dockerfile > /dev/null")
        os.system(f"sudo docker rmi {ass_code} > /dev/null")
    except Exception as e:
        logging.error(e)
    

def save_file(file, path, file_type="standard"):
    """
    This saves a file to the supplied path
    """
    if file:
        filename = secure_filename(file.filename)
        if file_type == "requirements":
            filename = "requirements.txt"
        if file_type == "marking_script":
            filename = "marking.py"
        file.save("{}/{}".format(path, filename))
        return True
    else:
        return False
