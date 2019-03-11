import os

class LODSchemaHandler():

	def __init__(self, config):
		self.config = config

	def getSchema(self, mimeType='text/turtle'):
		f = open(self.config['SCHEMA_FILE'], 'r')
		s = f.read()
		return s, mimeType

	#TODO: How to serve the Class paths? E.g. like /schema/format