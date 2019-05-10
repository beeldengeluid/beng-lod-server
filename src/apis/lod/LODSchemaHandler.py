import os
from util.APIUtil import APIUtil

class LODSchemaHandler():

	def __init__(self, config):
		self.config = config

	def getSchema(self):
		if os.path.exists(self.config['SCHEMA_FILE']):
			f = open(self.config['SCHEMA_FILE'], 'r')
			schema = f.read()
			f.close()
			return APIUtil.toSuccessResponse(schema)
		return APIUtil.toErrorResponse('internal_server_error', 'The schema file could not be found')
