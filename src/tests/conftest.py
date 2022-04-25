from flask import Flask
import json
import os
import pytest
from lxml import etree


def get_active_profile(app):
    def_profile = app.config["PROFILES"][0]
    for p in app.config["PROFILES"]:
        if "default" in p and p["default"] is True:
            def_profile = p
            break
    return def_profile


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
def open_file():
    """Returns the contents of a file that is in the test directory."""

    def return_contents_of_file(test_path, fn):
        full_path = os.path.join(os.path.dirname(test_path), fn)
        if os.path.exists(full_path):
            with open(full_path) as f:
                return f.read()
        return None

    return return_contents_of_file


@pytest.fixture(scope="module")
def etree_parse_doc():
    """Returns the ElementTree resulting form parsing the XML document."""

    def parse(test_path, fn):
        full_path = os.path.join(os.path.dirname(test_path), fn)
        if os.path.exists(full_path):
            return etree.parse(full_path)
        return None

    return parse


"""------------------------ APPLICATION SETTINGS (VALID) ----------------------"""


@pytest.fixture(scope="session")
def application_settings():
    """Returns the application settings."""
    app = Flask(__name__)
    app.config.from_object("config.settings_example.Config")
    app.config["ACTIVE_PROFILE"] = get_active_profile(app)
    app.config["GLOBAL_CACHE"] = {}
    return app.config


"""------------------------ APPLICATION CLIENT (VALID & INVALID) ----------------------"""


@pytest.fixture(scope="session")
def application_client():
    """Returns the token and id that should be available in the application settings."""
    return {"id": "unit_test", "token": "hahahahahahWAT_EEN_TEST"}


@pytest.fixture(scope="session")
def invalid_application_client():
    return {"id": "FAKE", "token": "FAKE"}


"""------------------------ API CLIENTS FOR ON & OFFLINE TESTING ----------------------"""


@pytest.fixture(scope="session")
def flask_test_client():
    """Returns a basic Flask test client."""
    from server import app

    return app.test_client()


@pytest.fixture(scope="session")
def http_test_client(application_settings):
    """Returns an HTTP client that can send requests to local server."""
    import requests

    class HTTPClient:
        def post(self, path, data=None):
            return requests.post(
                "http://localhost:%s%s" % (application_settings["APP_PORT"], path),
                json=data,
            )

        def get(self, path):
            return requests.get(
                "http://localhost:%s%s" % (application_settings["APP_PORT"], path)
            )

    return HTTPClient()


@pytest.fixture(scope="session")
def generic_client(http_test_client, flask_test_client):
    """Returns a GenericClient instance that either:
    returns the response from an HTTP client that sends requests to a Flask server,
    or, when offline, returns the response from a Flask test client that sends
    requests to a local Flask server.
    """

    class Response(object):
        def __init__(self, text, status_code, headers):
            self.text = text
            self.status_code = status_code
            self.headers = headers

    class GenericClient:
        def post(self, mode, path, data=None):
            if mode == "offline":
                r = flask_test_client.post(
                    path, data=json.dumps(data), content_type="application/json"
                )
                return Response(r.data, r.status_code, r.headers)
            else:
                return http_test_client.post(path, data=data)

        def get(self, mode, path):
            if mode == "offline":
                r = flask_test_client.get(path)
                return Response(r.data, r.status_code, r.headers)
            else:
                return http_test_client.get(path)

    return GenericClient()
