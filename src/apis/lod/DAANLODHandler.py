
from urllib.parse import urlencode
from util.APIUtil import APIUtil
from models.NISVRdfConcept import NISVRdfConcept
import urllib.request
import models.DAANJsonModel as model
import xmltodict


class DAANLODHandler(object):
    """ OAI-PMH provider serves catalogue data on a URL,
    # http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
    This class gets the XML from the URL, converts it to json, then uses the mapping
    information from the schema to create RDF from the json,
    """

    def __init__(self, config):

        # check config
        self.config = config

    def getOAIRecord(self, level, identifier, returnFormat):
        """Constructs a URI from the level and identifier, retrieves the record data from the URI,
        and returns LOD for the record in the desired return format"""
        url = self._prepareURI(level, identifier)
        try:
            data = self._OAI2LOD(url, returnFormat)
        except ValueError as e:
            return APIUtil.toErrorResponse('bad_request', e)

        if data:
            return APIUtil.toSuccessResponse(data)
        return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

    def _prepareURI(self, level, identifier):
        """ Constructs valid OAI-PMH url from the config settings, the level and the identifier.
            e.g. http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
        """
        params = {
            'verb': 'GetRecord',
            'metadataPrefix': 'fe',
            'identifier': ':'.join(['oai', level, identifier])
        }
        path = 'oai'
        base_url = '/'.join([self.config['OAI_BASE_URL'], path])
        return '?'.join([base_url, urlencode(params)])

    def _OAI2LOD(self, url, returnFormat):
        """ Returns the record data from a URL, transformed to RDF, loaded
        in a Graph and serialized to target format."""

        # retrieve the record data in XML via OAI-PMH
        xmlString = self._getXMLFromOAI(url)

        # transform the XML to RDF
        resultConcept = self._transformXMLToRDF(xmlString)

        # serialise the RDF graph to desired format
        data = resultConcept.serialize(returnFormat)
        return data

    def _transformXMLToRDF(self, xmlString):
        """Transforms the XML to json and then to RDF using the schema mapping"""

        xmlString = xmlString.replace("fe:", "")  # remove the namespace prefix, we don't need it
        json = xmltodict.parse(xmlString)  # convert the XML to json

        if "OAI-PMH" in json:  # work-around as the test XML files are not accepted by PyCharm as valid XML with the OAI-PMH header in
            if "error" in json["OAI-PMH"]:
                raise ValueError("Retrieving concept from OAI-PMH failed %s" % json["OAI-PMH"]["error"])

            record = json["OAI-PMH"]["GetRecord"]["record"]
        else:  # this is the case for the test XML files
            record = json["GetRecord"]["record"]

        # get the type - series, season etc.
        setSpec = record["header"]["setSpec"].upper()

        # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
        if setSpec == model.ObjectType.LOGTRACKITEM.value:
            logtrackType = record["metadata"]["entry"]["logtrack_type"]
            if not model.isSceneDescription(logtrackType):
                raise ValueError(
                    "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrackType)

        rdfConcept = NISVRdfConcept(record["metadata"]["entry"], setSpec, self.config)

        return rdfConcept

    def _getXMLFromOAI(self, url):
        """Retrieves an XML string from the given OAI-PMH url"""
        response = urllib.request.urlopen(
            url)
        data = ""
        for line in response:
            data += line.decode('utf-8')

        return data
