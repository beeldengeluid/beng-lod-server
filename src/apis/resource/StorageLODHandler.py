import logging

from util.APIUtil import APIUtil
import urllib.request
import json
from urllib.error import HTTPError
from urllib.parse import urlparse, urlunparse
import requests
from requests.exceptions import ConnectionError


class StorageLODHandler:
    """ Base class for a LOD Handler that either serves NISV schema data, or
        schema.org. Other formats can get their own handler.
        The payload from the STORAGE API is used as input to serve catalogue data on a URI.
    """
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.config['LOG_NAME'])

    def get_profile(self, profile_uri):
        profile = None
        if 'PROFILES' in self.config:
            for p in self.config['PROFILES']:
                if p['uri'] == profile_uri:
                    profile = p
                    break
        return profile

    def get_storage_record(self, level, identifier, return_format):
        """ Constructs a URI from the level and identifier, retrieves the record metadata from the
         DM API URI, and returns LOD for the record in the desired return format.
         :param level: cat type ('program', 'series', 'season', 'scene')
         :param identifier: the DAAN id
         :param return_format: the Accept type, like 'text/turtle, etc.'
         :returns: a response object
         """
        try:
            url = self._prepare_storage_uri(level, identifier)
            data = self._storage_2_lod(url, return_format)
            if data:
                return APIUtil.toSuccessResponse(data)
            return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

        except ValueError as e:
            self.logger.debug('ValueError caused 400')
            return APIUtil.toErrorResponse('bad_request', e)
        except urllib.error.HTTPError as e:
            self.logger.debug('HTTPError caused 404')
            return APIUtil.toErrorResponse('not_found', e)
        except Exception as err:
            self.logger.exception('Exception')

        return APIUtil.toErrorResponse('internal_server_error')

    def _prepare_storage_uri(self, level, identifier):
        """ Constructs valid Storage url from the config settings, the level (cat type) and the identifier.
                <storage URL>/storage/<TYPE>/<id>
            When <TYPE> is 'scene' it needs to be replaced with 'logtrackitem' for the storage API.
        :param level: the cat type (program, series, season, scene)
        :param identifier: the DAAN id
        :returns: a proper URI for getting metadata from the DM API
        """
        url_parts = urlparse(self.config.get('STORAGE_BASE_URL'))
        if url_parts.netloc is not None:
            if level == 'scene':
                path = '/'.join(['storage', 'logtrackitem', str(identifier)])
            else:
                path = '/'.join(['storage', level, str(identifier)])
            parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
            return urlunparse(parts)
        else:
            return None

    def _get_json_from_storage(self, url):
        """ Retrieves a JSON object from the given Storage url
            Description: http://acc-app-bng-01.beeldengeluid.nl:8101/storage/doc
            :param url: the URI for the resource to get the data for.
            :returns: the data or None
        """
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                if self.config.get('LOG_LEVEL_CONSOLE', None) == 'DEBUG':
                    with open('last_request.json', 'w') as f:
                        json.dump(resp.text, f, indent=4)
                return json.loads(resp.text)
        except ConnectionError as con_err:
            self.logger.exception('ConnectionError')
        except json.decoder.JSONDecodeError as json_err:
            self.logger.exception(JSONDecodeError)
        except Exception as err:
            self.logger.exception('Exception')
        return None

    def _storage_2_lod(self, url, return_format):
        """ Returns the record data from a URL, transformed to RDF, loaded in a Graph and
            serialized to target format.
        """
        # retrieve the record data in JSON from DM API
        json_data = self._get_json_from_storage(url)
        assert isinstance(json_data, dict), 'No valid results from the flex store.'

        # transform the JSON to RDF
        result_object = self._transform_json_to_rdf(json_data)

        # serialise the RDF graph to desired format
        data = result_object.serialize(return_format)
        return data

    """ Methods below need to be overwritten by the derived class
    """
    def _transform_json_to_rdf(self, json_obj):
        """ Transforms JSON data from the flex Direct Access Metadata API to RDF.
        Derived Classes need to implement this.
        """
        raise NotImplementedError()
