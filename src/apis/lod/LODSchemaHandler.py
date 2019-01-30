import requests
# from os.path import expanduser

class LODSchemaHandler(object):
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
		server = u':'.join([config['APP_HOST'],config['APP_PORT']])
		self.base_url = u'/'.join([protocol,server,path,filename])
		
	def getSchema(self,mimeType='text/turtle'):
		r = requests.get(self.base_url)
		print r.url
		return r.text, mimeType
	