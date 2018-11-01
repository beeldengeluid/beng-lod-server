import json

from flask import current_app, request, Response
from flask_restplus import Api, Namespace, fields, Resource

from apis.lod.LODHandler import LODHandler

api = Namespace('lod', description='LOD')

#generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- GENERIC ANNOTATION ENDPOINTS -------------------------- """

@api.doc(params={'programId': 'The program ID'}, required=False)
@api.route('resource/<level>/<identifier>', endpoint='dereference')
class LODAPI(Resource):

	@api.response(200, 'Success', responseModel)
	@api.response(404, 'Resource does not exist error')
	def get(self, level, identifier):
		#http://oaipmh.beeldengeluid.nl/resource/program/5382355?output=bg
		acceptType = request.headers.get('Accept-Type')
		returnFormat = 'xml'
		if acceptType:
			if acceptType.find('rdf/xml') != -1:
				returnFormat = 'rdf/xml'
		resp, mimeType = LODHandler(current_app.config).getOAIRecord(level, identifier, returnFormat)

		if resp and mimeType:
			return Response(resp, mimetype=mimeType)
		return 'dikke pech gozert'
