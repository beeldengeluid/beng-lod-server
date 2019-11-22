from rdflib import Graph, URIRef
from rdflib.plugin import PluginException
from urllib.parse import urlencode
from util.APIUtil import APIUtil
import urllib.request
import models.import_models as model
# import models.import_schema as schema
from models.DAANSchemaImporter import DAANSchemaImporter, NISV_NAMESPACE, NISV_PREFIX
from rdflib.namespace import Namespace, NamespaceManager, SKOS
import xmltodict
from rdflib.namespace import XSD

# URIs for concepts in the schema
PROGRAM = NISV_NAMESPACE + "Program"
SEASON = NISV_NAMESPACE + "Season"
SERIES = NISV_NAMESPACE + "Series"
CARRIER = NISV_NAMESPACE + "Carrier"
CLIP = NISV_NAMESPACE + "SceneDescription"
ACTING_ENTITY = NISV_NAMESPACE + "ActingEntity"
HAS_DAAN_PATH = NISV_NAMESPACE + "hasDaanPath"
HAS_CARRIER = NISV_NAMESPACE + "hasCarrier"
IS_PART_OF_SERIES = NISV_NAMESPACE + "isPartOfSeries"
IS_PART_OF_SEASON = NISV_NAMESPACE + "isPartOfSeason"
IS_PART_OF_PROGRAM = NISV_NAMESPACE + "isPartOfProgram"

# list of non-gtaa types, so we can use the correct namespace for concepts of this type
NON_GTAA_TYPES = [NISV_NAMESPACE + "TargetGroup", NISV_NAMESPACE + "Broadcaster", NISV_NAMESPACE + "BroadcastStation",
                  NISV_NAMESPACE + "Language"]

GTAA_NAMESPACE = "http://data.beeldengeluid.nl/gtaa/"
NON_GTAA_NAMESPACE = "http://data.beeldengeluid.nl/nongtaa/"

XSD_TYPES = [str(XSD.string), str(XSD.int), str(XSD.float), str(XSD.boolean), str(XSD.long), str(XSD.dateTime),
             str(XSD.date)]

# URIs to use for different levels of DAAN records
CLASS_URIS_FOR_DAAN_LEVELS = {"SERIES": SERIES, "SEASON": SEASON, "PROGRAM": PROGRAM, "LOGTRACKITEM": CLIP,
                              "ITEM": CARRIER}


class LODHandler(object):
    """ OAI-PMH provider serves catalogue data on a URL,
		# http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
		This class gets the XML from the URL, converts it to json, then uses the mapping
		information from the schema to create RDF from the json,
	"""

    def __init__(self, config):

        # check config
        self.config = config
        if "SCHEMA_FILE" not in self.config or "MAPPING_FILE" not in self.config:
            raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'Schema or mapping file not specified')

        # set up namespace manager for RDF graph
        nisvNamespace = Namespace(NISV_NAMESPACE)
        self.namespaceManager = NamespaceManager(Graph())
        self.namespaceManager.bind(NISV_PREFIX, nisvNamespace)
        self.namespaceManager.bind("skos", SKOS)

        # load classes and their mappings to DAAN from RDF schema
        self._schema = DAANSchemaImporter(self.config["SCHEMA_FILE"], self.config["MAPPING_FILE"])
        self._classes = self._schema.getClasses()

        assert self._classes is not None, APIUtil.raiseDescriptiveValueError('internal_server_error',
                                                                             'Error while loading the schema classes and properties')

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

    def serializeGraph(self, graph, returnFormat):
        """ Serialize graph data to requested format."""
        try:
            return graph.serialize(format=returnFormat)

        except PluginException as e:
            print(e)
        except Exception as e:
            print('serializeGraph => ')
            print(e)

    def _OAI2LOD(self, url, returnFormat):
        """ Returns the record data from a URL, transformed to RDF, loaded
			in a Graph and serialized to target format."""

        # retrieve the record data in XML via OAI-PMH
        xmlString = self._getXMLFromOAI(url)

        # transform the XML to RDF
        result = self._transformXMLToRDF(xmlString)

        # serialise the RDF graph to desired format
        data = self.serializeGraph(result, returnFormat)
        return data

    def _transformXMLToRDF(self, xmlString):
        """Transforms the XML to json and then to RDF using the schema mapping"""
        graph = Graph()
        graph.namespace_manager = self.namespaceManager
        xmlString = xmlString.replace("fe:", "")  # remove the namespace prefix, we don't need it
        json = xmltodict.parse(xmlString)  # convert the XML to json

        if "OAI-PMH" in json:  # work-around as the test XML files are not accepted by PyCharm as valid XML with the OAI-PMH header in
            if "error" in json["OAI-PMH"]:
                raise ValueError("Retrieving concept from OAI-PMH failed %s" % json["OAI-PMH"]["error"])

            record = json["OAI-PMH"]["GetRecord"]["record"]
        else:  # this is the case for the test XML files
            record = json["GetRecord"]["record"]

        # create a node for the record
        itemNode = URIRef(record["metadata"]["entry"]["id"])

        # get the type - series, season etc.
        setSpec = record["header"]["setSpec"]

        # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
        if setSpec == model.ObjectType.LOGTRACKITEM.value:
            logtrackType = record["metadata"]["entry"]["logtrack_type"]
            if not model.isSceneDescription(logtrackType):
                raise ValueError(
                    "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrackType)

        # get the RDF class URI for this type
        classUri = CLASS_URIS_FOR_DAAN_LEVELS[setSpec]

        # convert the record payload to RDF
        model.payloadToRdf(record["metadata"]["entry"]["payload"], itemNode, classUri, self._classes, graph)

        # create RDF relations with the parents of the record
        model.parentToRdf(record["metadata"]["entry"], itemNode, classUri, graph)

        return graph

    def _getXMLFromOAI(self, url):
        """Retrieves an XML string from the given OAI-PMH url"""
        response = urllib.request.urlopen(
            url)
        data = ""
        for line in response:
            data += line.decode('utf-8')

        return data
