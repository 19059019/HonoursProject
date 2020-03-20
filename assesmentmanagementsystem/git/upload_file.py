#!/usr/bin/env python
import gitlab
import base64

GIT_SERVER = "http://0.0.0.0:30080"
TOKEN = "uftVvHy_5j1vJw2kcwtt"

gl = gitlab.Gitlab(GIT_SERVER, private_token=TOKEN)

project = gl.projects.get(1)

with open("gitlab_scripts.py", "r") as wololo:
    try:
        f = project.files.create(
            {
                "file_path": "gitlab_scripts.py",
                "branch": "master",
                "content":wololo.read(),
                "author_email": "root@root.co.za",
                "author_name": "root",
                "commit_message": "Create testfile",
            }
        )
    except Exception as e:
        print(e)