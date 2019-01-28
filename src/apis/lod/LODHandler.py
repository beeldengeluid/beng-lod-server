import requests
from rdflib import Graph
from lxml import etree
# from io import BytesIO
from lxml.etree import XSLTError
from os.path import expanduser
from logging.config import IDENTIFIER

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
		
		#TODO: remove hard coded paths... move them to config?
		home = expanduser("~")
		local = 'eclipse-workspace'
		repo = 'beng-lod-server'
		self._resource = 'resource'
		xslt = 'nisv-bg-oai2lod-v01.xsl'
		self.base_url = 'http://oaipmh.beeldengeluid.nl/resource/'
		
		# uncomment if local server is needed
		protocol = 'file://'
		self.local_base_url = '/'.join([protocol,home,local,repo,self._resource])
		
# 		self._xsltfile = '/'.join([home, 'eclipse-workspace','beng-lod-server','resource','nisv-bg-oai2lod-v01.xsl'])
		self._xsltfile = '/'.join([home,local,repo,self._resource,xslt])
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
		# TODO: make this an OAI-PMH GetRecord request
		# http://oaipmh.beeldengeluid.nl/oai?verb=GetRecord&metadataPrefix=bg&identifier=oai:program:3883163
		print '/'.join([self.local_base_url,level,identifier])
		return '/'.join([self.local_base_url,level,identifier])
		return 'http://oaipmh.beeldengeluid.nl/resource/%s/%s?output=bg' % (level, identifier)

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
