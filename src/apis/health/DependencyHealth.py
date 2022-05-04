from dataclasses import dataclass
from http import HTTPStatus
import logging
from typing import Optional

import requests
from requests.exceptions import RequestException, URLRequired


@dataclass
class DependencyHealth:
    status_code: Optional[HTTPStatus]

    def is_ok(self):
        return self.status_code == HTTPStatus.OK


@dataclass
class Dependency:
    config_key: str
    health_url: str

    def get_health(self, timeout_sec: float) -> DependencyHealth:
        # try to get a response from self.health_url. on errors that are
        # likely due to the dependency, set the http_status to None.
        logging.info("Getting health response for '%s'" % self.health_url)

        try:
            health_response = requests.get(self.health_url, timeout=timeout_sec)
        except (URLRequired, ValueError):
            logging.exception("Cannot get health response for '%s'" % self.health_url)
            raise
        except RequestException:
            logging.exception("Cannot get health respsonse for '%s'" % self.health_url)
            http_status = None
        else:
            logging.info("Got response for '%s'" % self.health_url)
            http_status = HTTPStatus(health_response.status_code)

        return DependencyHealth(http_status)
