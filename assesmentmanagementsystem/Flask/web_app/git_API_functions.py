from config import *
import gitlab

GIT_SERVER = config["git_server"]
TOKEN = config["git_token"]

gl = gitlab.Gitlab(GIT_SERVER, private_token=TOKEN)

