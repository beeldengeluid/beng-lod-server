from rdflib import Graph, URIRef
from rdflib.plugin import PluginException
from urllib.parse import urlencode
from util.APIUtil import APIUtil
import urllib.request
import models.import_models as model
import models.import_schema as schema
from rdflib.namespace import Namespace, NamespaceManager, SKOS
import xmltodict

class LODHandler(object):
	''' OAI-PMH provider serves catalogue data on a URL,
		# http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
		This class enables getting the XML from the URL, transform to RDF/XML using an XSLT,
	'''
	def __init__(self, config):
		nisvNamespace = Namespace(schema.NISV_NAMESPACE)
		self.namespaceManager = NamespaceManager(Graph())
		self.namespaceManager.bind(schema.NISV_PREFIX, nisvNamespace)
		self.namespaceManager.bind("skos", SKOS)
		self.config = config

		if "SCHEMA_FILE" not in self.config or "MAPPING_FILE" not in self.config:
			raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'Schema or mapping file not specified')

		self.classes = schema.importSchema(self.config["SCHEMA_FILE"], self.config["MAPPING_FILE"])

		if not self.classes:
			raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'Error while loading the schema classes and properties')


	def getOAIRecord(self, level, identifier, returnFormat):
		url = self._prepareURI(level, identifier)
		data = self._OAI2LOD(url, returnFormat)
		if data:
			return APIUtil.toSuccessResponse(data)
		return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

	def _prepareURI(self, level, identifier):
		""" Returns valid OAI-PMH url.
				e.g. http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
		"""
		params = {
			'verb':				'GetRecord',
			'metadataPrefix':	'fe',
			'identifier':		':'.join(['oai', level, identifier])
		}
		path = 'oai'
		base_url = '/'.join([self.config['OAI_BASE_URL'], path])
		return '?'.join([base_url, urlencode(params)])


	def serializeGraph(self, graph, returnFormat):
		""" Serialize data to requested format."""
		try:
			return graph.serialize(format=returnFormat)

		except PluginException as e:
			print(e)
		except Exception as e:
			print('serializeGraph => ')
			print(e)

	def _OAI2LOD(self, url, returnFormat):
		""" Returns the data from a URL transformed to RDF/XML, loaded
			in a Graph and serialized to target format."""
		try:
			xmlString = self._getXMLFromOAI(url)
			result = self._transformXMLToRDF(xmlString)
			data = self.serializeGraph(result, returnFormat)
			return data
		except Exception as e:
			print(e)

	def _transformXMLToRDF(self, xmlString):
		graph = Graph()
		graph.namespace_manager = self.namespaceManager
		xmlString = xmlString.replace("fe:", "")
		json = xmltodict.parse(xmlString)
		itemNode = URIRef(json["GetRecord"]["record"]["metadata"]["entry"]["id"])

		setSpec = json["GetRecord"]["record"]["header"]["setSpec"]

		if setSpec == model.ObjectType.LOGTRACKITEM.name:
			logtrackType = json["GetRecord"]["record"]["metadata"]["entry"]["logtrack_type"]
			if logtrackType != model.LogTrackType.SCENE_DESC:
				return APIUtil.toErrorResponse('bad_request', "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc"%logtrackType)

		classUri = schema.CLASS_URIS_FOR_DAAN_LEVELS[setSpec]

		model.payloadToRdf(json["GetRecord"]["record"]["metadata"]["entry"]["payload"], itemNode, classUri,self.classes, graph)
		model.parentToRdf(json["GetRecord"]["record"]["metadata"]["entry"], itemNode, classUri, graph)

		return graph

	def _getXMLFromOAI(self, url):
		file = urllib.urlopen(
			url)
		data = file.read()
		file.close()

		return data
