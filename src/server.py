import sys
import logging
import re
from util.base_util import LOG_FORMAT
from flask import Flask, redirect, request
from flask_cors import CORS
from apis import api
from util.base_util import validate_config

app = Flask(__name__)

# init the config
app.config.from_object("config.settings.Config")
app.config["CORS_HEADERS"] = "Content-Type"
app.config["RESTPLUS_VALIDATE"] = False
app.config["GLOBAL_CACHE"] = {}  # just put the cache in here

# logger = init_logger(app)
# initialises the root logger
logging.basicConfig(
    level=app.config["LOG_LEVEL"],
    stream=sys.stdout,  # configure a stream handler only for now (single handler)
    format=LOG_FORMAT,
)
logger = logging.getLogger()


if not validate_config(app.config):
    logger.error("Invalid config, quitting")
    quit()

app.debug = app.config["DEBUG"]

CORS(app)

app.url_map.strict_slashes = False


@app.before_request
def clear_trailing():
    rp = request.path
    pattern = "^/(id|gtaa)/?(.*)$"
    match = re.fullmatch(pattern, rp)
    if match is None:
        return "Page not found", 404
    if rp != "/" and rp.endswith("/"):
        return redirect(rp[:-1])


def get_active_profile():
    def_profile = app.config["PROFILES"][0]
    for p in app.config["PROFILES"]:
        if "default" in p and p["default"] is True:
            def_profile = p
            break
    return def_profile


# TODO now the active profile is static and cannot be defined via the URL
app.config["ACTIVE_PROFILE"] = get_active_profile()

api.init_app(
    app,
    title="Open Data Lab API - Netherlands Institute for Sound and Vision",
    description="Get RDF for open datasets and for resources in the NISV catalogue.",
)

if __name__ == "__main__":
    app.run(host=app.config["APP_HOST"], port=app.config["APP_PORT"])
