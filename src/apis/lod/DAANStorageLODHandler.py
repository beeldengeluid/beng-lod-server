from util.APIUtil import APIUtil
from models.NISVRdfConcept import NISVRdfConcept
from models.SDORdfConcept import SDORdfConcept
import urllib.request
from models.DAANJsonModel import DAAN_TYPE, ObjectType, isSceneDescription
import json
from urllib.error import HTTPError


class DAANStorageLODHandler(object):
    """ STORAGE API serves catalogue data on a URL,
    This class gets the JSON from the URL, then uses the mapping
    information from the schema to create RDF from the json,
    """

    def __init__(self, config):

        # check config
        self.config = config

    def getStorageRecord(self, level, identifier, return_format):
        """Constructs a URI from the level and identifier, retrieves the record data from the URI,
        and returns LOD for the record in the desired return format"""
        url = self._prepareURI(level, identifier)
        try:
            data = self._storage2LOD(url, return_format)
        except ValueError as e:
            return APIUtil.toErrorResponse('bad_request', e)
        except urllib.error.HTTPError as e:
            return APIUtil.toErrorResponse('not_found', e)

        if data:
            return APIUtil.toSuccessResponse(data)
        return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

    def _prepareURI(self, level, identifier):
        """ Constructs valid Storage url from the config settings, the level (type) and the identifier.
            <storage URL>/storage/<TYPE>/<id>
        """
        if self.config.get('STORAGE_BASE_URL') is not None:
            return "%s/storage/%s/%s" % (self.config.get('STORAGE_BASE_URL'), level, identifier)
        else:
            return None

    def _storage2LOD(self, url, return_format):
        """ Returns the record data from a URL, transformed to RDF, loaded
        in a Graph and serialized to target format.
        # TODO: test whether the return_format parameter can be given the mimetype
        """

        # retrieve the record data in XML via OAI-PMH
        json_data = self._getJsonFromStorage(url)

        # TODO: make the data profile configurable, e.g. nisv or sdo
        # transform the XML to RDF
        result_concept = self._transformJSONToRDF(json_data)

        # serialise the RDF graph to desired format
        data = result_concept.serialize(return_format)
        return data

    def _transform_json_to_sdo(self, json_obj):
        """ Transforms JSON data from the flex Direct Access Metdata API to schema.org
            # TODO: refactor NISVRdfConcept for SDO to SDOVRdfConcept
        """
        # get the type - series, season etc.
        set_spec = json_obj[DAAN_TYPE]

        # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
        if set_spec == ObjectType.LOGTRACKITEM.value:
            logtrack_type = json_obj["logtrack_type"]
            if not isSceneDescription(logtrack_type):
                raise ValueError(
                    "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrack_type)

        rdf_concept = SDOVRdfConcept(json_obj, set_spec, self.config)
        return rdf_concept

    def _transformJSONToRDF(self, json_obj):
        """Transforms the json to RDF using the schema mapping"""

        # get the type - series, season etc.
        set_spec = json_obj[DAAN_TYPE]

        # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
        if set_spec == ObjectType.LOGTRACKITEM.value:
            logtrack_type = json_obj["logtrack_type"]
            if not isSceneDescription(logtrack_type):
                raise ValueError(
                    "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrack_type)
        rdf_concept = NISVRdfConcept(json_obj, set_spec, self.config)
        return rdf_concept

    def _getJsonFromStorage(self, url):
        """Retrieves a JSON object from the given Storage url"""
        with urllib.request.urlopen(
                url) as storageUrl:
            data = json.loads(storageUrl.read().decode())

        return data
