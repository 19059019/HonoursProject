#!/usr/bin/env python2
from functions import *
from git_handler import *
from cli_functions import *
from git_API_functions import *
from models import *
from config import *
from flask_cas import CAS, login, logout, login_required
from werkzeug import secure_filename
import os
import csv
import json
import logging
import jinja2
from flask import (
    Flask,
    request,
    session,
    redirect,
    url_for,
    render_template,
    flash,
    send_from_directory,
    Response,
    make_response,
)

# Initial directory system setup
setup_directories()

logging.basicConfig(level=logging.DEBUG)
UPLOAD_FOLDER = "uploaded"

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

cas = CAS(app, "/cas")
app.config["CAS_SERVER"] = "https://sso-prod.sun.ac.za"
app.config["CAS_AFTER_LOGIN"] = "index"


@app.before_request
def before_request_callback():
    session["user"] = cas.username
    session["title"] = User(session["user"]).title


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico")


@app.route("/")
@login_required
def index():
    USER = User(session["user"])
    response = make_response(
        render_template(
            "index.html",
            modules=USER.modules,
            assignments=USER.assignments,
            subs_made=get_subs_made(USER),
        )
    )
    return response


@app.route("/set_cookie")
@login_required
def set_vm_cookie():
    USER = User(session["user"])
    if session["title"] == "admin":
        response = make_response(
            render_template(
                "index.html", modules=USER.modules, assignments=USER.assignments
            )
        )
        response.set_cookie(
            "uuid",
            "True",
            expires=datetime.datetime.now() + datetime.timedelta(days=1000),
        )
        return response
    else:
        return redirect("/")


@app.route("/modules/<module>", methods=["GET", "POST"])
@login_required
def manage_modules(module):
    USER = User(session["user"])
    if module in get_modules():
        return view_assignment(module)
    if request.method == "POST":
        add_user(request.form)
    return render_template(
        "manage_modules.html", modules=USER.modules, assignments=USER.assignments
    )


@app.route("/create", methods=["GET", "POST"])
@login_required
def create_assignment():
    error = {}
    if request.method == "POST":
        gen_assignment(request)
        return redirect(url_for("index"))
    USER = User(session["user"])
    return render_template(
        "create_assignment.html",
        modules=USER.modules,
        assignments=USER.assignments,
        error=error,
    )


@app.route("/download/<ass_code>")
@login_required
def download(ass_code):
    """
    Expose assignment files for download if allowed
    """
    path, filename = get_files_path(ass_code)
    logging.info("{} Sending {} from {}".format(session["user"], filename, path))
    user = User(session["user"])
    if path and ass_code in user.assignments_list:
        return send_from_directory(
            path, filename, as_attachment=True, attachment_filename=(str(filename))
        )
    else:
        return json.dumps(
            {
                "Error": "File Download is currently not available",
                "Status": "Incident for {} has been logged".format(session["user"]),
            }
        )


@app.route("/toggle_late/<ass_code>/<source>")
@login_required
def toggle_late(ass_code, source):
    """
    Allows a lecturer to toggle whether late submissions are allowed or not
    """
    if session["title"] in ["admin", "lecturer"]:
        toggle_late_submissions(ass_code)
        if source == "assignment":
            return redirect(url_for("view_assignment"))
        else:
            return redirect(url_for("index"))
    else:
        return json.dumps({"Error": "Insufficient Permissions"})


@app.route("/consent")
@login_required
def consent():
    """
    Returns the electronic permission consent form
    """
    path = "./resources/documents"
    filename = "Consent.pdf"
    return send_from_directory(
        path, filename, as_attachment=True, attachment_filename=(str(filename))
    )


@app.route("/download_ass_files/<ass_code>")
@login_required
def download_ass_files(ass_code):
    path = "modules/{}/{}/assignment_files/downloads"
    path = path.format(ass_code[:5], ass_code)
    if os.path.exists(path):
        tar_bz2_dir(path, ass_code, "download")
        filename = os.listdir(path)[0]
        return send_from_directory(
            path, filename, as_attachment=True, attachment_filename=(str(filename))
        )
    else:
        return "No files available for {}".format(ass_code)


@app.route("/download_submission/<ass_code>/<suid>")
@login_required
def download_submission(ass_code, suid):
    """ 
    this function allows demis and markers to download
    the specific submission by a student for an assignment.
    """
    if session["title"] == "student":
        if str(session["user"]) != str(suid):
            return json.dumps({"Error": "Insufficient permissions"})
    filename = "{}_submission.tar.bz2".format(ass_code)
    module = ass_code[:5]
    # create tar.bz2
    path = "modules/{}/{}/submissions/{}".format(module, ass_code, suid)
    try:
        # delete tar.bz2 if an older version exists
        if os.path.exists(path + "/" + filename):
            os.remove(path + "/" + filename)
        path = tar_bz2_dir(path, ass_code, "submission")
        # send tar.bz2
        return send_from_directory(
            path, filename, as_attachment=True, attachment_filename=(filename)
        )
    except Exception as e:
        logging.error(e)
        return redirect("/report/{}".format(ass_code))


@app.route("/download_submissions/<ass_code>")
@login_required
def download_submissions(ass_code):
    """ 
    this function allows demis and markers to download
    the submissions for an assignment.
    """
    if session["title"] == "student":
        return "error"
    filename = "{}_submissions.tar.bz2".format(ass_code)
    module = ass_code[:5]
    # create tar.bz2
    path = "./modules/{}/{}".format(module, ass_code)
    # delete tar.bz2 if an older version exists
    if os.path.exists(path + "/" + filename):
        os.remove(path + "/" + filename)
    path = tar_bz2_dir(path, ass_code, "submissions")
    # send tar.bz2
    return send_from_directory(
        path, filename, as_attachment=True, attachment_filename=(filename)
    )


@app.route("/download_marking/<ass_code>")
@login_required
def download_marking(ass_code):
    """ 
    this function allows demis and markers to download
    the marking logs from an assignment.
    """
    if session["title"] == "student":
        return "error"
    filename = "{}_logs_complete.tar.bz2".format(ass_code)
    try:
        module = ass_code[:5]
        # create tar.bz2
        path = "../marking/logs"
        # delete tar.bz2 if an older version exists
        if os.path.exists(path + "/" + filename):
            os.remove(path + "/" + filename)
        log_files = os.listdir(path)
        ass_logs = [x for x in log_files if ass_code in x]
        path = "{}/{}".format(path, ass_logs[0])
        path = tar_bz2_dir(path, "{}_logs".format(ass_code), "complete")
        # send tar.bz2
        return send_from_directory(
            path, filename, as_attachment=True, attachment_filename=(filename)
        )
    except Exception as e:
        logging.error(e)
        return marking()


@app.route("/assignment/<ass_code>", methods=["GET", "POST"])
@login_required
def assignment(ass_code):
    """
    Render a specific assignment
    """
    USER = User(session["user"])
    su_id = session["user"]
    error = {}
    if request.method == "POST":
        if allowed_submission(su_id, request.form["ass_code"]):
            if not handle_submission(request, session["user"]):
                error["error"] = "submission error"
            else:
                error = {}
        else:
            error["error"] = "submission error"
    else:
        return render_template(
            "view_assignments.html",
            assignments=USER.get_assignment(ass_code),
            subs_made=get_subs_made(USER),
            subs_allowed=get_resubmissions_allowed(USER),
            git_server=GIT_SERVER,
            error=error,
            modules=USER.modules,
        )


@app.route("/assignments", methods=["GET", "POST"])
@login_required
def view_assignment(module="none"):
    """ Render and handle assignments """
    # POST of this is a submission
    USER = User(session["user"])
    su_id = session["user"]
    error = {}
    if request.method == "POST":
        if allowed_submission(su_id, request.form["ass_code"]):
            if not handle_submission(request, session["user"]):
                error["error"] = "submission error"
            else:
                error = {}
        else:
            error["error"] = "submission error"

    u = User(session["user"])
    if module == "none":
        return render_template(
            "view_assignments.html",
            assignments=u.assignments,
            subs_made=get_subs_made(u),
            subs_allowed=get_resubmissions_allowed(u),
            git_server=GIT_SERVER,
            error=error,
            modules=USER.modules,
        )
    else:
        return render_template(
            "view_assignments.html",
            assignments=u.module_assignments(module),
            subs_made=get_subs_made(u),
            subs_allowed=get_resubmissions_allowed(u),
            git_server=GIT_SERVER,
            error=error,
            modules=USER.modules,
        )


@app.route("/1337", methods=["GET"])
@login_required
def easter_egg():
    return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@app.route("/admin", methods=["GET"])
@login_required
def easter_egg_admin():
    return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@app.route("/report/<ass_code>", methods=["GET"])
@login_required
def reporting(ass_code):
    stats = get_assignment_stats(ass_code)
    USER = User(session["user"])

    if session["title"] == "student":
        return redirect("/")
    else:
        module = ass_code[:5]
        ass = {}
        with open(
            "modules/{}/{}/assignment_files/sub.json".format(module, ass_code)
        ) as sub:
            ass = json.load(sub)
        # commits,submissions,latest_submission,env_id,latest_ip,from_env, env_start, env_end, pipeline status, pipeline link, download
        logs_template = [
            "0",
            "0",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
        ]
        module = Module(module)
        path = "modules/{}/{}/assignment_files/logs.csv".format(module.module, ass_code)
        git = False
        with open(
            "modules/{}/{}/assignment_files/sub.json".format(module.module, ass_code)
        ) as sub:
            sub = json.load(sub)
            if sub["git"] == "true":
                git = True
                logging.debug("Reporting Git")
        users = {}
        if os.path.isfile(path):
            users = module.get_students()
            with open(path, "r") as logs:
                logs = csv.reader(logs, delimiter=",")
                first = True
                for log in logs:
                    if first:
                        first = not first
                        continue
                    else:
                        users[log[0]] = log[1:] + 6 * [None]
            for user in users:
                if len(users[user]) == 0:
                    users[user] = logs_template
                    # pipeline
                users[user][10] = "../download_submission/{}/{}".format(ass_code, user)
                if git == True:
                    git_path = "assessmentmanagementsystem/{}/{}/{}_{}".format(
                        module.module, ass_code, ass_code, user
                    )
                    logging.debug("Project at {}".format(git_path))
                    project = gl.projects.get(git_path)
                    pipeline = project.pipelines.list()[0]
                    pipeline_status = pipeline.status
                    pipeline_link = "{}/assessmentmanagementsystem/{}/{}/{}_{}/pipelines/{}".format(
                        config["git_server"],
                        module.module,
                        ass_code,
                        ass_code,
                        user,
                        pipeline.id,
                    )
                    users[user][8] = pipeline_status
                    users[user][9] = pipeline_link
        return render_template(
            "reporting.html",
            ass=ass,
            users=users,
            modules=USER.modules,
            assignments=USER.assignments,
            stats=stats,
        )


@app.route("/submit", methods=["POST"])
@login_required
def submit_cli():
    su_id = session["user"]
    if request.method == "POST" and allowed_submission(su_id, request.form["ass_code"]):
        handle_submission(request, su_id)
        return "Successful submission."
    else:
        return "Error: Submission not valid."


@app.route("/test_submit/<su_id>", methods=["POST"])
@login_required
def test_submit_cli(su_id):
    if session["title"] != "admin":
        return {"Error": "Unauthorised"}
    if request.method == "POST" and allowed_submission(su_id, request.form["ass_code"]):
        logging.debug("Test Submision being handled")
        handle_submission(request, su_id)
        return json.dumps({"Message": "Successful submission."})
    else:
        return json.dumps({"Error": "Submission not valid."})


@app.route("/create_assignment_cli", methods=["GET", "POST"])
@login_required
def create_assignment_cli():
    """
    This will accept a submission and/or env json and create assignments.
    A get request will 
    """
    if session["title"] == "student":
        return "error"
    if request.method == "POST":
        if len(request.files) > 0:
            sub = None
            env = None
            logging.info("Files: {}".format(request.files.keys()))
            if "sub.json" in request.files.keys():
                sub = request.files["sub.json"].read()
            if "env.json" in request.files.keys():
                env = request.files["env.json"].read()
            if env != None or sub != None:
                return gen_assignment_cli(sub, env, request)

        return "Error: Invalid upload"
    else:
        filename = tar_bz2_templates()
        return send_from_directory(
            "resources", filename, as_attachment=True, attachment_filename=(filename)
        )


@app.route("/env/<ass_code>", methods=["GET"])
@login_required
def send_env(ass_code):
    filename = "env.json"
    path = "modules/{}/{}/assignment_files".format(ass_code[:5], ass_code)
    user = User(session["user"])
    if not ass_code in user.assignments_list:
        return json.dumps({"error": "Not valid assignment"})
    return send_from_directory(
        path, filename, as_attachment=True, attachment_filename=(filename)
    )


@app.route("/env-action/<action>", methods=["POST"])
@login_required
def cli_env_action(action):
    if action == "start":
        # Handle env start
        env_start(request)
        pass
    elif action == "end":
        # Handle env end
        env_end(request)
        pass
    else:
        return json.dumps({"error": "Invalid action"})
    return json.dumps({"success": "True"})


@app.route("/testloggedin")
@login_required
def test_logged_in():
    return "true"


@app.route("/marking", methods=["GET", "POST"])
@login_required
def marking():
    """ Render and handle marking """
    # POST of this is a submission
    USER = User(session["user"])
    su_id = session["user"]
    error = {}
    if request.method == "POST" and (USER.title == "lecturer" or USER.title == "admin"):
        if not mark_assignment(request):
            error[
                "Error"
            ] = "Marking server timeout. Try again or contact an admin if the problem persists"

    return render_template(
        "marking.html", error=error, modules=USER.modules, assignments=USER.assignments
    )


@app.route("/git-push", methods=["POST", "GET"])
def git_push_hook():
    if request.method == "GET":
        return json.dumps({"Response": "URL Exists"})
    data = json.loads(request.data)
    if data["event_name"] == "push":
        handle_git_push(data)
        return json.dumps({"success": True})
    else:
        return json.dumps({"success": False})


if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0")
