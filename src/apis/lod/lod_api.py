from flask import current_app, request, Response
from flask_restplus import Api, Namespace, fields, Resource

from apis.lod.LODHandler import LODHandler
from apis.lod.LODSchemaHandler import LODSchemaHandler

api = Namespace('lod', description='LOD')
api2 = Namespace('schema', description='Schema')

#generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- RESOURCE ENDPOINT -------------------------- """
@api.route('resource/<level>/<identifier>', endpoint='dereference')
class LODAPI(Resource):

    @api.response(404, 'Resource does not exist error')
#     @api.representation('application/rdf+xml','application/ld+json','text/turtle','text/n3')
    def get(self, level, identifier):
        acceptType = request.headers.get('Accept')

        # mapping from mimetype to rdflib formats
        serializeMimetype = {}     
        serializeMimetype['application/rdf+xml']    = 'xml'
        serializeMimetype['application/ld+json']    = 'json-ld'
        serializeMimetype['text/turtle']            = 'ttl'
        serializeMimetype['text/n3']                = 'n3'
        
        mimetype = 'application/rdf+xml'
        if acceptType.find('rdf+xml') != -1:
            mimetype = 'application/rdf+xml'
        elif acceptType.find('json+ld') != -1:
            mimetype = 'application/ld+json'
        elif acceptType.find('json') != -1:
            mimetype = 'application/ld+json'
        elif acceptType.find('turtle') != -1:
            mimetype = 'text/turtle'
        elif acceptType.find('json') != -1:
            mimetype = 'text/n3'

        returnFormat = serializeMimetype[mimetype]
        
        resp = LODHandler(current_app.config).getOAIRecord(level, identifier, returnFormat)
        
        if resp and mimetype:
            return Response(resp[0], mimetype=mimetype)
        return 'dikke pech gozert'

""" --------------------------- SCHEMA ENDPOINT -------------------------- """

@api.route('schema', endpoint='schema')
class LODSchemaAPI(Resource):

    @api.response(404, 'Schema does not exist error')
    def get(self):
        mimeType = 'text/turtle'
        resp, mimeType = LODSchemaHandler(current_app.config).getSchema(mimeType=mimeType)

        if resp and mimeType:
            return Response(resp, mimetype=mimeType)
        return 'ooeei, een hele dikke bug'
