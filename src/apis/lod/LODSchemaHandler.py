import os
from util.APIUtil import APIUtil

#TODO I think this class is obsolete

class LODSchemaHandler():

	def __init__(self, config):
		self.config = config

	def getSchema(self):
		if os.path.exists(self.config['ACTIVE_PROFILE']['schema']):
			f = open(self.config['ACTIVE_PROFILE']['schema'], 'r')
			schema = f.read()
			f.close()
			return APIUtil.toSuccessResponse(schema)
		return APIUtil.toErrorResponse(
			'internal_server_error', 'The schema file %s could not be found'.format(
				self.config['ACTIVE_PROFILE']['schema']
			)
		)
