import logging
from typing import List, Tuple

from flask import current_app
from flask_restx import Namespace, Resource

from apis.health.DependencyHealth import Dependency, DependencyHealth

api = Namespace(
    "Health",
    description="Overall health of the API.",
)


@api.hide
@api.route("health")
class Health(Resource):
    def get(self):
        logging.info("Determining health of dependencies")
        health_timeout_sec = current_app.config["HEALTH_TIMEOUT_SEC"]
        dependencies = [
            Dependency(
                "SPARQL_ENDPOINT",
                current_app.config["SPARQL_ENDPOINT_HEALTH_URL"],
            )
        ]
        dependency_health: List[Tuple[Dependency, DependencyHealth]] = [
            (dependency, dependency.get_health(health_timeout_sec))
            for dependency in dependencies
        ]
        dependencies_ok = all(health.is_ok() for _, health in dependency_health)

        # ...
        # additional health checks could be implemented here
        # ...

        logging.info("Determining overall health")
        health = {
            dependency.config_key: {
                "url": dependency.health_url,
                "statusCode": health.status_code,
            }
            for dependency, health in dependency_health
        }

        health_status = 200 if dependencies_ok else 500
        return health, health_status
