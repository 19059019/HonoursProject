from functions import *
import tarfile
import json
import csv
import re
import os


def gen_assignment_cli(sub_json, env_json, request):
    """
    This handles assignment generation from a CLI post request
    with the setup files
    """
    pattern = "^\d\d\d\d-(0?[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(00|0[0-9]|1[0-9]|2[0-3]):(0[0-9]|[0-5][0-9])$"
    if sub_json != None:
        sub_json = json.loads(sub_json)
        if not re.match(pattern, sub_json["start"]) or not re.match(
            pattern, sub_json["end"]
        ):
            return "Error: Invalid start or end time, please use the format yyyy-MM-ddThh:mm"
        if sub_json["Title"] == "":
            return "Error: Title required"
        module = sub_json["module"]
        ass_code = gen_directories(module)
        sub_json["Ass_Code"] = ass_code
        path = "modules/{}/{}/assignment_files/".format(sub_json["module"], ass_code)
        add_logs_file(path, ass_code)
        with open("{}sub.json".format(path), "w") as outfile:
            json.dump(sub_json, outfile)
        if env_json != None:
            env_json = json.loads(env_json)
            with open("{}env.json".format(path), "w") as outfile:
                json.dump(env_json, outfile)
        if sub_json["file"] == "true":
            path = "{}downloads".format(path)
            os.mkdir(path)
        if sub_json["git"] == "true":
            try:
                gen_repositories(ass_code, request)
            except Exception as e:
                logging.error(e)
        return "success"
    return "Error: Missing submision configuration file"
    # TODO:Generate Scripts


def tar_bz2_templates():
    """
    This fetches the templates needed to create an assignment from the CLI
    """
    with tarfile.open("resources/create_submission_files.tar.bz2", "w:bz2") as tar:
        tar.add(
            "resources/sub_template.json",
            arcname=os.path.basename("resources/sub_template.json"),
        )
        tar.add(
            "resources/env_template.json",
            arcname=os.path.basename("resources/env_template.json"),
        )
    return "create_submission_files.tar.bz2"