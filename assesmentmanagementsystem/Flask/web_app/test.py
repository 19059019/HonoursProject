#!/usr/bin/env python

from config import *
from git_API_functions import *
print([gl.users.list(username="amstest{}".format(x)) for x in range(0, 8)])