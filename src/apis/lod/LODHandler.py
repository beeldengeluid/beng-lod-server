import os
from rdflib import Graph
from rdflib.plugin import PluginException
from lxml import etree
from lxml.etree import XSLTError
from urllib import urlencode
from util.APIUtil import APIUtil

class LODHandler(object):
	''' OAI-PMH provider serves catalogue data on a URL,
		e.g.: http://oaipmh.beeldengeluid.nl/resource/program/5296881?output=bg
			# TODO: make this an OAI-PMH GetRecord request
			# http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
		This class enables getting the XML from the URL, transform to RDF/XML using an XSLT,
	'''
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

	#Returns valid OAI-PMH url, e.g. http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
	def _prepareURI(self, level, identifier):
		params = {
			'verb':				'GetRecord',
			'metadataPrefix':	'bg',
			'identifier':		':'.join(['oai', level, identifier])
		}
		path = 'oai'
		base_url = '/'.join([self.config['OAI_BASE_URL'], path])
		return '?'.join([base_url, urlencode(params)])

	def _OAI2LOD(self, url, returnFormat):
		root = etree.parse(
			url,
			parser=etree.XMLParser(remove_blank_text=True, compact=False, ns_clean=True, recover=True)
		).getroot()

		try:
			result = self.transformer(root)
			graph = Graph()
			graph.parse(data=etree.tostring(result, xml_declaration=True))
			return graph.serialize(context=result.getroot().nsmap, format=returnFormat)
		except XSLTError as e:
			for error in self.transformer.error_log:
				print(error.message, error.line)
		except PluginException as e:
			print(e)
		except Exception as e:
			print(e)
		return None
