import os
from util.APIUtil import APIUtil
from flask import Flask, current_app


class LODSchemaHandler:

    def __init__(self, config):
        self.config = config

    def getSchema(self):
        # make sure the path can be read (use app context)
        # see https://flask.palletsprojects.com/en/1.1.x/appcontext/
        app = Flask(__name__)
        with app.app_context():
            app_path = os.path.dirname(os.path.realpath(current_app.instance_path))
            schema_filename = os.path.join(app_path, self.config['SCHEMA_FILE'])

        if os.path.exists(schema_filename):
            f = open(schema_filename, 'r')
            schema = f.read()
            f.close()
            return APIUtil.toSuccessResponse(schema)
        return APIUtil.toErrorResponse('internal_server_error', 'The schema file could not be found')
