import os
from flask import Flask
from pathlib import Path


def getBasePath():
    """Gets the base path of the application"""
    pathElements = __file__.split(os.sep)
    reversePathElements = __file__.split(os.sep)[::-1]
    basePath = os.sep.join(pathElements[:-reversePathElements.index("beng-lod-server")])
    return basePath


def get_base_path():
    """
    Gets the root path for a Flask application, no matter what OS or user.
    """
    app = Flask(__name__)
    with app.app_context():
        app_directory = Path(app.root_path).parents[1]
        return app_directory
