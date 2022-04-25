from flask import Flask, Response  # redirect, send_from_directory
from flask_cors import CORS
from apis import api
from util.base_util import init_logger, validate_config

app = Flask(__name__)

# init the config
app.config.from_object("config.settings.Config")
app.config["CORS_HEADERS"] = "Content-Type"
app.config["RESTPLUS_VALIDATE"] = False
app.config["GLOBAL_CACHE"] = {}  # just put the cache in here

logger = init_logger(app)

if not validate_config(app.config):
    logger.error("Invalid config, quitting")
    quit()

app.debug = app.config["DEBUG"]

CORS(app)


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

"""------------------------------------------------------------------------------
PING / HEARTBEAT ENDPOINT
------------------------------------------------------------------------------"""


@app.route("/ping")
def ping():
    logger.debug("Received ping")
    return Response("pong", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host=app.config["APP_HOST"], port=app.config["APP_PORT"])
