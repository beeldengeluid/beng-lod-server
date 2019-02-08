import os

class LODSchemaHandler():

	def __init__(self, config):
		self.config = config

	def getSchema(self, mimeType='text/turtle'):
		f = open(os.path.join(self.config['RESOURCE_DIR'], 'bengSchema.ttl'), 'r')
		s = f.read()
		return s, mimeType
	
	#TODO: How to server the Class paths? E.g. like /schema/format