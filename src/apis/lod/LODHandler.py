import os
from rdflib import Graph
from rdflib.plugin import PluginException
from lxml import etree
from lxml.etree import XSLTError
from urllib.parse import urlencode
from util.APIUtil import APIUtil


class LODHandler(object):
	""" OAI-PMH provider serves catalogue data on a URL,
		# http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
		This class enables getting the XML from the URL, transform to RDF/XML using an XSLT,
	"""
	def __init__(self, config):
		self.config = config

		if not os.path.exists(self.config['XSLT_FILE']):
			raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'XLST_FILE could not be found on the file system')

		self.transformer = self._getXSLTTransformer(self.config['XSLT_FILE'])

		if not self.transformer:
			raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'Error while parsing the XLST')

	def _getXSLTTransformer(self, xsltFile):
		xslTree = etree.parse(
			xsltFile,
			parser=etree.XMLParser(remove_comments=True, ns_clean=True, no_network=False)
		)
		return etree.XSLT(xslTree)

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
			'metadataPrefix':	'bg',
			'identifier':		':'.join(['oai', level, identifier])
		}
		path = 'oai'
		base_url = '/'.join([self.config['OAI_BASE_URL'], path])
		return '?'.join([base_url, urlencode(params)])

	def getElementTreeFromXMLDoc(self, url):
		""" Returns an ElementTree, that represents the XML document at the given URL.."""
		try:
			doctree = etree.parse(
				url,
				parser=etree.XMLParser(remove_blank_text=True, compact=False, ns_clean=True, recover=True)
			)
			return doctree
		except Exception as e:
			print(e)

	def transformFromDocTree(self, docTree):
		""" doc is an ElementTree from an XML document.
			After transformation with XSLT, the resulting tree as RDF/XML is returned.
		"""
		try:
			root = docTree.getroot()
			return self.transformer(root)
		except XSLTError as e:
			print(e)
			for error in self.transformer.error_log:
				print(error.message, error.line)

	def loadAndSerializeGraph(self, et, returnFormat):
		""" Parse from string into graph, then serialize data to requested format."""
		try:
			graph = Graph()
			xmldata = etree.tostring(et, encoding='unicode')
			graph.parse(data=xmldata)
			xmlns = et.getroot().nsmap
			return graph.serialize(context=xmlns, format=returnFormat)

		except PluginException as e:
			print(e)
		except Exception as e:
			print('loadAndSerializeGraph => ')
			print(e)

	def _OAI2LOD(self, url, returnFormat):
		""" Returns the data from a URL transformed to RDF/XML, loaded
			in a Graph and serialized to target format."""
		try:
			doctree = self.getElementTreeFromXMLDoc(url)
			result = self.transformFromDocTree(doctree)
			data = self.loadAndSerializeGraph(result, returnFormat)
			return data
		except Exception as e:
			print(e)
