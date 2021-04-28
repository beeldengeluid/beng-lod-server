from util.APIUtil import APIUtil
import urllib.request
import json
from urllib.error import HTTPError
from urllib.parse import urlparse, urlunparse


class StorageLODHandler:
    """ STORAGE API serves catalogue data on a URL.
        This class is a base class for a LOD Handler that either serves NISV schema data, or
        schema.org. Other formats can get their own handler.
    """
    def __init__(self, config):
        # check config
        self.config = config

    def get_storage_record(self, level, identifier, return_format):
        """Constructs a URI from the level and identifier, retrieves the record data from the URI,
        and returns LOD for the record in the desired return format"""
        url = self._prepare_uri(level, identifier)
        try:
            data = self._storage_2_lod(url, return_format)
        except ValueError as e:
            return APIUtil.toErrorResponse('bad_request', e)
        except urllib.error.HTTPError as e:
            return APIUtil.toErrorResponse('not_found', e)

        if data:
            return APIUtil.toSuccessResponse(data)
        return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

    def _prepare_uri(self, level, identifier):
        """ Constructs valid Storage url from the config settings, the level (type) and the identifier.
            <storage URL>/storage/<TYPE>/<id>
        """
        url_parts=urlparse(self.config.get('STORAGE_BASE_URL'))
        if url_parts.netloc is not None:
            path = '/'.join(['storage', level, identifier])
            parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
            return urlunparse(parts)
        else:
            return None

    @staticmethod
    def _get_json_from_storage(url):
        """Retrieves a JSON object from the given Storage url"""
        with urllib.request.urlopen(
                url) as storageUrl:
            data = json.loads(storageUrl.read().decode())
        return data

    def _storage_2_lod(self, url, return_format):
        """ Returns the record data from a URL, transformed to RDF, loaded in a Graph and
            serialized to target format.
        TODO: find out if the return_format parameter can be given the mimetype. Refactor for json-ld.
        """

        # retrieve the record data in XML via OAI-PMH
        json_data = self._get_json_from_storage(url)

        # transform the XML to RDF
        result_concept = self._transform_json_to_rdf(json_data)

        # serialise the RDF graph to desired format
        # TODO: find out how to get rid of this warning
        data = result_concept.serialize(return_format)
        return data

    """ Methods below need to be overwritten by the derived class
    """
    def _transform_json_to_rdf(self, json_obj):
        """ Transforms JSON data from the flex Direct Access Metadata API to RDF.
        """
        pass

    #
    #
    # def _transform_json_to_rdf(self, json_obj):
    #     """ Transforms JSON data from the flex Direct Access Metadata API to schema.org
    #         # TODO: refactor NISVRdfConcept for SDO to SDOVRdfConcept
    #     """
    #     # get the type - series, season etc.
    #     set_spec = json_obj[DAAN_TYPE]
    #
    #     # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
    #     if set_spec == ObjectType.LOGTRACKITEM.value:
    #         logtrack_type = json_obj["logtrack_type"]
    #         if not isSceneDescription(logtrack_type):
    #             raise ValueError(
    #                 "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrack_type)
    #
    #     rdf_concept = SDORdfConcept(json_obj, set_spec, self.config)
    #     return rdf_concept
    #
    # def _transform_json_to_rdf(self, json_obj):
    #     """Transforms the json to RDF using the schema mapping"""
    #
    #     # get the type - series, season etc.
    #     set_spec = json_obj[DAAN_TYPE]
    #
    #     # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
    #     if set_spec == ObjectType.LOGTRACKITEM.value:
    #         logtrack_type = json_obj["logtrack_type"]
    #         if not isSceneDescription(logtrack_type):
    #             raise ValueError(
    #                 "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrack_type)
    #     rdf_concept = NISVRdfConcept(json_obj, set_spec, self.config)
    #     return rdf_concept
