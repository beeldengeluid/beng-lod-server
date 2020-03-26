
from util.APIUtil import APIUtil
from models.NISVRdfConcept import NISVRdfConcept
import urllib.request
from models.DAANJsonModel import DAAN_TYPE, ObjectType, isSceneDescription
import json


class DAANStorageLODHandler(object):
    """ STORAGE API serves catalogue data on a URL,
    This class gets the JSON from the URL, then uses the mapping
    information from the schema to create RDF from the json,
    """

    def __init__(self, config):

        # check config
        self.config = config

    def getStorageRecord(self, level, identifier, returnFormat):
        """Constructs a URI from the level and identifier, retrieves the record data from the URI,
        and returns LOD for the record in the desired return format"""
        url = self._prepareURI(level, identifier)
        try:
            data = self._storage2LOD(url, returnFormat)
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
        return "%s/storage/%s/%s"%(self.config['STORAGE_BASE_URL'], level, identifier)


    def _storage2LOD(self, url, returnFormat):
        """ Returns the record data from a URL, transformed to RDF, loaded
        in a Graph and serialized to target format."""

        # retrieve the record data in XML via OAI-PMH
        xmlString = self._getJsonFromStorage(url)

        # transform the XML to RDF
        resultConcept = self._transformJSONToRDF(xmlString)

        # serialise the RDF graph to desired format
        data = resultConcept.serialize(returnFormat)
        return data

    def _transformJSONToRDF(self, json):
        """Transforms the json to RDF using the schema mapping"""

        # get the type - series, season etc.
        setSpec = json[DAAN_TYPE]

        # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
        if setSpec == ObjectType.LOGTRACKITEM.value:
            logtrackType = json["logtrack_type"]
            if not isSceneDescription(logtrackType):
                raise ValueError(
                    "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrackType)

        rdfConcept = NISVRdfConcept(json, setSpec, self.config)

        return rdfConcept

    def _getJsonFromStorage(self, url):
        """Retrieves a JSON object from the given Storage url"""
        with urllib.request.urlopen(
            url) as storageUrl:
            data = json.loads(storageUrl.read().decode())

        return data
