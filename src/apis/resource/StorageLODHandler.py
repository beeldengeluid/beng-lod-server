import logging
from util.APIUtil import APIUtil
import json
from urllib.error import HTTPError
from urllib.parse import urlparse, urlunparse
import requests
from requests.exceptions import ConnectionError


class StorageLODHandler:
    """Base class for a LOD Handler that either serves NISV schema data, or
    schema.org. Other formats can get their own handler.
    The payload from the STORAGE API is used as input to serve catalogue data on a URI.
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.config["LOG_NAME"])

    def get_profile(self, profile_uri):
        profile = None
        if "PROFILES" in self.config:
            for p in self.config["PROFILES"]:
                if p["uri"] == profile_uri:
                    profile = p
                    break
        return profile

    def get_storage_record(self, level, identifier, return_format):
        """Constructs a URI from the level and identifier, retrieves the record metadata from the
        DM API URI, and returns LOD for the record in the desired return format.
        :param level: cat type ('program', 'series', 'season', 'scene')
        :param identifier: the DAAN id
        :param return_format: the Accept type, like 'text/turtle, etc.'
        :returns: a response object
        """
        use_file_logger = self.config.get("LOG_LEVEL_CONSOLE", None) == "DEBUG"
        try:
            url = self._prepare_storage_uri(
                self.config.get("STORAGE_BASE_URL"), level, identifier
            )
            data = self._storage_2_lod(url, return_format, use_file_logger)
            if data:
                return APIUtil.toSuccessResponse(data)
            return APIUtil.toErrorResponse(
                "bad_request", "That return format is not supported"
            )

        except ValueError as e:
            self.logger.debug("ValueError caused 400")
            return APIUtil.toErrorResponse("bad_request", e)
        except HTTPError as e:
            self.logger.debug("HTTPError caused 404")
            return APIUtil.toErrorResponse("not_found", e)
        except Exception:
            self.logger.exception("Exception")

        return APIUtil.toErrorResponse("internal_server_error")

    def _prepare_storage_uri(self, storage_base_url: str, level: str, identifier: int):
        """Constructs valid Storage url from the config settings, the level (cat type) and the identifier.
                {storage_base_url}/storage/<TYPE>/<id>
            When <TYPE> is 'scene' it needs to be replaced with 'logtrackitem' for the storage API.
            More information: {storage_base_url}/storage/doc
        :param storage_base_url: server providing api services
        :param level: the cat type (program, series, season, scene)
        :param identifier: the DAAN id
        :returns: a proper URI for getting metadata from the DM API
        """
        url_parts = urlparse(storage_base_url)
        if url_parts.netloc is not None and url_parts.netloc != "":
            if level == "scene":
                path = "/".join(["storage", "logtrackitem", str(identifier)])
            else:
                path = "/".join(["storage", level, str(identifier)])
            parts = (url_parts.scheme, url_parts.netloc, path, "", "", "")
            return urlunparse(parts)
        return None

    def _get_json_from_storage(self, url: str, use_file_logger: bool = False):
        """Retrieves a JSON object from the given Storage url
        :param url: the URI for the resource to get the data for.
        :param use_file_logger: flag for using logger
        :returns: the data or None
        """
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                if use_file_logger:
                    self._log_json_to_file(resp.text)
                return json.loads(resp.text)
        except ConnectionError:
            self.logger.exception("ConnectionError")
        except json.decoder.JSONDecodeError:
            self.logger.exception("JSONDecodeError")
        except Exception:
            self.logger.exception("Exception")
        return None

    def _log_json_to_file(self, json_data):
        with open("last_request.json", "w") as f:
            json.dump(json_data, f, indent=4)

    def _storage_2_lod(
        self, url: str, return_format: str, use_file_logger: bool = False
    ):
        """Returns the record data from a URL, transformed to RDF, loaded in a Graph and
        serialized to target format.
        :param url: requested url
        :param return_format: required serialization format
        :param use_file_logger: flag for using logger
        """
        # retrieve the record data in JSON from DM API
        json_data = self._get_json_from_storage(url, use_file_logger)
        assert isinstance(json_data, dict), "No valid results from the flex store."

        # transform the JSON to RDF
        result_object = self._transform_json_to_rdf(json_data)

        # serialise the RDF graph to desired format
        data = result_object.serialize(return_format)
        return data

    """ Methods below need to be overwritten by the derived class
    """

    def _transform_json_to_rdf(self, json_obj):
        """Transforms JSON data from the flex Direct Access Metadata API to RDF.
        Derived Classes need to implement this.
        """
        raise NotImplementedError()
