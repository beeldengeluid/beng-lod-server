import logging
from util.APIUtil import APIUtil
import json
from json.decoder import JSONDecodeError
from urllib.parse import urlparse, urlunparse
import requests
from requests.exceptions import ConnectionError, HTTPError

logger = logging.getLogger()


class StorageLODHandler:
    """Base class for a LOD Handler that either serves NISV schema data, or
    schema.org. Other formats can get their own handler.
    The payload from the STORAGE API is used as input to serve catalogue data on a URI.
    """

    def __init__(self, config):
        self.config = config

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
        try:
            url = self._prepare_storage_uri(
                self.config.get("STORAGE_BASE_URL"), level, identifier
            )
            data = self._storage_2_lod(url, return_format)
            if data:
                return APIUtil.toSuccessResponse(data)
            logger.error(f"Could not get data from the flex store for {url}.")
            return APIUtil.toErrorResponse(
                "bad_request", "That return format is not supported"
            )

        except ValueError as e:
            logger.exception("ValueError caused 400.")
            return APIUtil.toErrorResponse("bad_request", e)
        except HTTPError as e:
            status_code = e.response.status_code
            if status_code == 403:
                logger.exception(f"Acces denied for {url}.")
                return APIUtil.toErrorResponse("access_denied", e)
            if status_code == 404:
                logger.exception(f"Not found for {url}.")
                return APIUtil.toErrorResponse("not_found", e)
        except Exception:
            logger.exception("Exception")
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

    def _get_json_from_storage(self, url: str):
        """Retrieves a JSON object from the given Storage url
        :param url: the URI for the resource to get the data for.
        :returns: the data or None
        """
        try:
            logger.info(f"Get data from the flex store for {url}.")
            resp = requests.get(url)
            resp.raise_for_status()
            if resp.status_code == 200:
                logger.debug(resp.text)
                return json.loads(resp.text)
        except (ConnectionError, JSONDecodeError):
            logger.exception(f"Cannot get json for '{url}'")

        logger.error(f"Not a proper response from the flex store for {url}.")
        return None

    def _storage_2_lod(self, url: str, return_format: str):
        """Returns the record data from a URL, transformed to RDF, loaded in a Graph and
        serialized to target format. When no data could be retrieved None is returned.
        :param url: requested url
        :param return_format: required serialization format
        """
        # retrieve the record data in JSON from DM API
        json_data = self._get_json_from_storage(url)
        if json_data is None:
            logger.error(f"Could not get JSON data from the flex store for {url}.")
            return None

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
