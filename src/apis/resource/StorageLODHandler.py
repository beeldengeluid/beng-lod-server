from util.APIUtil import APIUtil
import urllib.request
import json
from urllib.error import HTTPError
from urllib.parse import urlparse, urlunparse

# TODO rewrite using the requests library
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
            # TODO: configure that this is only active when the code is run in AWS.
            # if run in AWS is true, test for permission
            lod_url = self._prepare_lod_resource_uri(level, identifier)
            if not self.check_resource_public(resource_url=lod_url):
                return APIUtil.toErrorResponse('access_denied', 'The resource can not be dereferenced.')

            # get it
            url = self._prepare_uri(level, identifier)
            data = self._storage_2_lod(url, return_format)
        except ValueError as e:
            return APIUtil.toErrorResponse('bad_request', e)
        except urllib.error.HTTPError as e:
            return APIUtil.toErrorResponse('not_found', e)

        if data:
            return APIUtil.toSuccessResponse(data)
        return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

    def check_resource_public(self, resource_url):
        """ Fire a query to the public sparql endpoint. In case the resource is available, it is permitted
        for public access.
        :param resource_url: the resource to be checked.
        :return True (yes, public access allowed), False (no, not allowed to dereference)
        """
        try:
            # get the SPARQL endpoint from the config
            sparql_endpoint = self.config.get('SPARQL_ENDPOINT')
            query_ask = 'ASK {<%s> ?p ?o . }' % resource_url
            nisv_error = {}

            # prepare and get the data from the triple store
            resp = requests.get(sparql_endpoint, params={'query': query_ask, 'format': 'json'})

            if resp.status_code == 400:
                return nisv_error
            if resp.json().get('boolean'):
                return True
            else:
                return False
        except ConnectionError as e:
            print(str(e))
        except Exception as e:
            print(str(e))

    def _prepare_lod_resource_uri(self, level, identifier):
        """ Constructs valid url using the data domain, the level (cat type) and the identifier.
                <storage URL>/storage/<TYPE>/<id>
        :param level: the cat type
        :param identifier: the DAAN id
        :returns: a proper URI as it should be listed in the LOD server
        """
        url_parts = urlparse(self.config.get('BENG_DATA_DOMAIN'))
        if url_parts.netloc is not None:
            path = '/'.join(['id', level, str(identifier)])
            parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
            return urlunparse(parts)
        else:
            return None

    def _prepare_uri(self, level, identifier):
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
        """
        with urllib.request.urlopen(
                url) as storageUrl:
            data = json.loads(storageUrl.read().decode())
            with open('last_request.json', 'w') as f:
                json.dump(data, f, indent=4)
        return data

    def _storage_2_lod(self, url, return_format):
        """ Returns the record data from a URL, transformed to RDF, loaded in a Graph and
            serialized to target format.
        TODO: find out if the return_format parameter can be given the mimetype. Refactor for json-ld.
        """

        # retrieve the record data in JSON from DM API
        json_data = self._get_json_from_storage(url)

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
