import sys
import logging
from flask import Flask
from flask_cors import CORS
from apis import api
from util.base_util import LOG_FORMAT
from config import cfg

app = Flask(__name__)

# merge config with app config
app.config.update(
    cfg
)  # note: works als long as no existing nested config dict needs to be updated
app.config["CORS_HEADERS"] = "Content-Type"
app.config["RESTPLUS_VALIDATE"] = False
app.config["GLOBAL_CACHE"] = {}  # just put the cache in here

# initialises the root logger
logging.basicConfig(
    level=app.config["LOG_LEVEL"],
    stream=sys.stdout,  # configure a stream handler only for now (single handler)
    format=LOG_FORMAT,
)
logger = logging.getLogger()


app.debug = app.config["DEBUG"]

CORS(app)

app.url_map.strict_slashes = False


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
