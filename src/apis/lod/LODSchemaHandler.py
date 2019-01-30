import os

class LODSchemaHandler():

	def __init__(self, config):
		self.config = config

		#TODO: remove hard coded paths... move them to config?
# 		home = expanduser("~")
# 		local = 'eclipse-workspace'
# 		repo = 'beng-lod-server'
		path = u'schema'
# 		protocol = 'file:/'
		filename = u'bengSchema.ttl'
# 		self.base_url = u'/'.join([protocol,home,local,repo,path,filename])
		# TODO make sure it also works for the webserver
		protocol = u'http:/'

	def getSchema(self, mimeType='text/turtle'):
		f = open(os.path.join(self.config['RESOURCE_DIR'], 'bengSchema.ttl'), 'r')
		s = f.read()
		return s, mimeType