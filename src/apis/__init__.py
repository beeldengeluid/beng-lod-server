from flask_restx import Api
import logging
from .pong.pong_api import api as pong_api
from .health.health_api import api as health_api
from .dataset.dataset_api import api as dataset_api
from .resource.resource_api import api as resource_api
from .gtaa.gtaa_api import api as gtaa_api


logger = logging.getLogger(__name__)
use_prod_config = True


try:
    from config.settings import Config as prod_conf  # fails in unit test
except ImportError:
    use_prod_config = False
    from config.settings_example import Config as test_conf

apiVersion = "v0.3"
base_path = "/"
api = Api(version=apiVersion)
enabled_endpoints = []

try:
    if use_prod_config:
        enabled_endpoints = prod_conf.ENABLED_ENDPOINTS
    else:
        enabled_endpoints = test_conf.ENABLED_ENDPOINTS
except AttributeError:
    logger.warning(
        "Misconfiguration, please add ENABLED_ENDPOINTS, now disallowing all endpoints"
    )
    enabled_endpoints = []

if "dataset" in enabled_endpoints:
    api.add_namespace(dataset_api, path="%s" % base_path)

if "resource" in enabled_endpoints:
    api.add_namespace(resource_api, path="%s" % base_path)

if "gtaa" in enabled_endpoints:
    api.add_namespace(gtaa_api, path="%s" % base_path)

if "pong" in enabled_endpoints:
    api.add_namespace(pong_api, path="%s" % base_path)

if "health" in enabled_endpoints:
    api.add_namespace(health_api, path="%s" % base_path)
