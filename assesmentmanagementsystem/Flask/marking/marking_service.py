#!/usr/bin/python3
from functions import *
from flask import Flask,request
from flask_restful import Resource, Api
import hashlib
import config
import os
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)
api = Api(app)
logging.basicConfig(level=logging.DEBUG)

class Mark(Resource):

    def post(self):
        if not verify_token(request):
            return {'error':'Invalid API token'}
        resp = mark_assignment(request)
        logging.debug(resp)
        return resp

api.add_resource(Mark, '/mark')


if __name__ == '__main__':
    app.run(threaded=True, host="0.0.0.0", port=5001)