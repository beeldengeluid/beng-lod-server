import json

from flask import current_app, request
from flask_restplus import Api, Namespace, fields, Resource

#from LODHandler import LODHandler

api = Namespace('LOD', description='LOD')

#generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- GENERIC ANNOTATION ENDPOINTS -------------------------- """

@api.doc(params={'programId': 'The program ID'}, required=False)
@api.route('/program/<programId>', endpoint='dereference')
class LODAPI(Resource):

	@api.response(200, 'Success', responseModel)
	@api.response(404, 'Resource does not exist error')
	def get(self, programId):
		print('dereferencing %s' % programId)
		return {}#LODHandler(current_app.config).test()