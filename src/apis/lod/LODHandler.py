from rdflib import Graph
from lxml import etree
from lxml.etree import XSLTError
from os.path import expanduser
from urllib import urlencode

class LODHandler(object):
	''' OAI-PMH provider serves catalogue data on a URL, 
	    e.g.: http://oaipmh.beeldengeluid.nl/resource/program/5296881?output=bg
			# TODO: make this an OAI-PMH GetRecord request
			# http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
	    This class enables getting the XML from the URL, transform to RDF/XML using an XSLT,
	    and loadData in a Graph. 
	    Serialization in any format that RDFlib can handle.
	'''
	def __init__(self, config):
		self.config = config
		
		#TODO: adapt puppet script, so that the settings are right...
		self.config['RESOURCE_DIR']  = '../resource'
		self.config['XSLT_FILENAME'] = 'nisv-bg-oai2lod-v01.xsl'
		self.config['OAI_BASE_URL'] = 'http://oaipmh.beeldengeluid.nl'
		
		path = self.config['RESOURCE_DIR'] 
		xslt = self.config['XSLT_FILENAME']
		self.base_url = self.config['OAI_BASE_URL']
	
		# uncomment if local server is needed
# 		home = expanduser("~")
# 		local = 'eclipse-workspace'
# 		repo = 'beng-lod-server'
# 		self._protocol = 'file:/'
# 		self.base_url = u'/'.join([self._protocol,home,local,repo,self._path])
		
		self._xsltfile = u'/'.join([path,xslt])
		
		assert self._xsltfile

		parser = etree.XMLParser(remove_comments=True,ns_clean=True,no_network=False)
		xslTree = etree.parse(self._xsltfile, parser=parser)
		self._transform = etree.XSLT(xslTree)
		assert self._transform, '%s error: transformation is not loaded' % self.__class__.__name__

	def getOAIRecord(self, level, identifier, returnFormat):
		url = self.prepareURI(level, identifier)
		print url
		return self._OAI2LOD(url, returnFormat), returnFormat
	
	def prepareURI(self,level,identifier):
		# e.g. http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
		params = {}
		params['verb'] = 'GetRecord'
		params['metadataPrefix'] = 'bg'
		params['identifier'] = ':'.join(['oai', level, identifier])
		path = 'oai'
		base_url = '/'.join([self.base_url,path])
		full_url = '?'.join([base_url,urlencode(params)])
		return full_url

	def _OAI2LOD(self, url, returnFormat):
		parser = etree.XMLParser(remove_blank_text=True,compact=False,ns_clean=True,recover=True)
		root = etree.parse(url, parser=parser).getroot()

		try:
			result = self._transform(root)
			graph = Graph()
			graph.parse(data=etree.tostring(result, xml_declaration=True))
# 			print graph.serialize(	context=result.getroot().nsmap, 
# 											format=returnFormat)
			return graph.serialize(	context=result.getroot().nsmap, 
											format=returnFormat), returnFormat

		except XSLTError, e:
			for error in self._transform.error_log:
				print(error.message, error.line)

		except Exception,e:
			# Unknown error, exit for now (raise)
			print str(e)
			raise(e)
