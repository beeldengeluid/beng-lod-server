from flask_restx import Api
from .pong.pong_api import api as pong_api
from .health.health_api import api as health_api
from .dataset.dataset_api import api as dataset_api
from .resource.resource_api import api as resource_api

try:
    from config.settings import Config  # fails in unit test
except ImportError:
    from config.settings_example import Config

apiVersion = "v0.3"
base_path = "/"

api = Api(version=apiVersion)

try:
    enabled_endpoints = Config.ENABLED_ENDPOINTS
except AttributeError:
    print(
        "Misconfiguration, please add ENABLED_ENDPOINTS, now disallowing all endpoints"
    )
    enabled_endpoints = []

if "dataset" in enabled_endpoints:
    api.add_namespace(dataset_api, path="%s" % base_path)

if "resource" in enabled_endpoints:
    api.add_namespace(resource_api, path="%s" % base_path)

if "pong" in enabled_endpoints:
    api.add_namespace(pong_api, path="%s" % base_path)

if "health" in enabled_endpoints:
    api.add_namespace(health_api, path="%s" % base_path)
