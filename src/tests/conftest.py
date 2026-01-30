import json
import os
import pytest
from rdflib import Graph
from config import cfg


"""
Basic fixtures that are useful for most of the test modules
"""

"""------------------------ APPLICATION BASE PATH/URL ----------------------"""


@pytest.fixture(scope="session")
def base_path():
    """Return the base path for the application."""
    return os.sep


@pytest.fixture(scope="session")
def base_url(application_settings, base_path):
    """Returns the service URL."""
    return "http://localhost:%s%s" % (application_settings["APP_PORT"], base_path)


@pytest.fixture(scope="session")
def base_file_path():
    """Returns the base path for a file, excluding the filename (and extension)."""
    parts = os.path.realpath(__file__).split(os.sep)
    return os.sep.join(parts[0 : len(parts) - 2])


@pytest.fixture(scope="module")
def load_json_file():
    def return_json_data_from_file(test_path, fn):
        path = test_path
        tmp = test_path.split(os.sep)
        if len(tmp) > 1:
            path = os.sep.join(test_path.split(os.sep)[:-1])
        full_path = os.path.join(path, fn)
        if os.path.exists(full_path):
            return json.load(open(full_path, encoding="utf-8"))
        return None

    return return_json_data_from_file


@pytest.fixture(scope="module")
def load_file_as_graph():
    def return_graph_from_file(test_path, fn):
        path = test_path
        tmp = test_path.split(os.sep)
        if len(tmp) > 1:
            path = os.sep.join(test_path.split(os.sep)[:-1])
        full_path = os.path.join(path, fn)
        if os.path.exists(full_path):
            g = Graph()
            return g.parse(full_path)
        return None

    return return_graph_from_file


@pytest.fixture(scope="module")
def open_file():
    """Returns the contents of a file that is in the test directory."""

    def return_contents_of_file(test_path, fn):
        full_path = os.path.join(os.path.dirname(test_path), fn)
        if os.path.exists(full_path):
            with open(full_path) as f:
                return f.read()
        return None

    return return_contents_of_file


"""------------------------ APPLICATION SETTINGS (VALID) ----------------------"""


@pytest.fixture(scope="session")
def application_settings(flask_test_client):
    """Returns the application settings."""
    return flask_test_client.application.config


"""------------------------ API CLIENT ----------------------"""


@pytest.fixture(scope="session")
def flask_test_client():
    """Returns a basic Flask test client."""
    from server import app

    app.config.update(cfg)  # merge config with app config
    app.config["TESTING"] = True
    app.config["GLOBAL_CACHE"] = {}
    app.config["SERVER_NAME"] = "localhost:5000"

    return app.test_client()
