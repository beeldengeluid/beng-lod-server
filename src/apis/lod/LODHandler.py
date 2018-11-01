import lxml
import requests

class LODHandler(object):

	def __init__(self, config):
		self.config = config

	def test():
		print('implement this')
		pass

	def getOAIRecord(self, level, identifier, returnFormat):
		xml = self._getRecord(level, identifier)
		if returnFormat == 'xml':
			return xml, 'text/xml'
		elif returnFormat == 'rdf/xml':
			return '%s to be implemented' % returnFormat, 'text/plain'

		return '%s to be implemented' % returnFormat, 'text/plain'


	def _getRecord(self, level, identifier):
		url = 'http://oaipmh.beeldengeluid.nl/resource/%s/%s?output=bg' % (level, identifier)
		resp = requests.get(url)
		if resp.status_code == 200:
			return resp.text