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
            print(f"Fetching from storage: {url}")
            data = self._storage_2_lod(url, return_format)
            print(data)
            if data:
                return APIUtil.toSuccessResponse(data)
            return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

        except ValueError as e:
            return APIUtil.toErrorResponse('bad_request', e)
        except urllib.error.HTTPError as e:
            return APIUtil.toErrorResponse('not_found', e)
        except Exception as err:
            print(err)
            return APIUtil.toErrorResponse('internal_server_error', err)

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

    @staticmethod
    def _get_json_from_storage(url):
        """ Retrieves a JSON object from the given Storage url
            Description: http://acc-app-bng-01.beeldengeluid.nl:8101/storage/doc
            :param url: the URI for the resource to get the data for.
            :returns: the data or None
        """
        # try:
        #     app.logger.info('Testing the logger.')
        #     with urllib.request.urlopen(
        #             url) as storageUrl:
        #         data = json.loads(storageUrl.read().decode())
        #
        #         with open('last_request.json', 'w') as f:
        #             json.dump(data, f, indent=4)
        #     return data
        # except Exception as err:
        #     app.logger.error(str(err))

        # TODO rewrite using the requests library
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return json.loads(resp.text)
        except Exception as e:
            print('TODO implement proper error handling for:')
            print(e)
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
