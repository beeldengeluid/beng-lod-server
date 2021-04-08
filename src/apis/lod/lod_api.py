from flask import current_app, request, Response
from flask_restx import Namespace, fields, Resource

# from apis.lod.DAANLODHandler import DAANLODHandler
from apis.lod.DAANStorageLODHandler import DAANStorageLODHandler
from apis.lod.LODHandlerConcept import LODHandlerConcept
# from apis.lod.LODSchemaHandler import LODSchemaHandler

api = Namespace('lod', description='LOD')

# generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- RESOURCE ENDPOINT -------------------------- """


@api.route('resource/<level>/<identifier>', endpoint='dereference')
class LODAPI(Resource):

    MIME_TYPE_TO_LD = {
        'application/rdf+xml' : 'xml',
        'application/ld+json' : 'json-ld',
        'text/turtle' : 'ttl',
        'text/n3' : 'n3'
    }

    LD_TO_MIME_TYPE = {v: k for k, v in MIME_TYPE_TO_LD.items()}

    def _extractDesiredFormats(self, accept_type):
        mimetype = 'application/rdf+xml'
        if accept_type.find('rdf+xml') != -1:
            mimetype = 'application/rdf+xml'
        elif accept_type.find('json+ld') != -1:
            mimetype = 'application/ld+json'
        elif accept_type.find('json') != -1:
            mimetype = 'application/ld+json'
        elif accept_type.find('turtle') != -1:
            mimetype = 'text/turtle'
        elif accept_type.find('json') != -1:
            mimetype = 'text/n3'
        return mimetype, self.MIME_TYPE_TO_LD[mimetype]

    @api.response(404, 'Resource does not exist error')
    def get(self, level, identifier):
        accept_type = request.headers.get('Accept')
        user_format = request.args.get('format', None)
        mimetype, ld_format = self._extractDesiredFormats(accept_type)

        # override the accept format if the user specifies a format
        if user_format and user_format in self.LD_TO_MIME_TYPE:
            ld_format = user_format
            mimetype = self.LD_TO_MIME_TYPE[user_format]

        # resp, status_code, headers = DAANLODHandler(current_app.config).getOAIRecord(level, identifier, ldFormat)
        resp, status_code, headers = DAANStorageLODHandler(current_app.config).getStorageRecord(level, identifier,
                                                                                                ld_format)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


""" --------------------------- GTAA ENDPOINT -------------------------- """


@api.route('concept/<set_code>/<notation>', endpoint='concept')
class LODConceptAPI(Resource):

    MIME_TYPE_TO_LD = {
        'application/rdf+xml': 'xml',
        'application/ld+json': 'json-ld',
        'text/turtle': 'ttl',
        'text/n3': 'n3'
    }

    LD_TO_MIME_TYPE = {v: k for k, v in MIME_TYPE_TO_LD.items()}

    def _extractDesiredFormats(self, acceptType):
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
        return mimetype, self.MIME_TYPE_TO_LD[mimetype]

    # TODO: how to use the representations:
    #  https://flask-restx.readthedocs.io/en/latest/_modules/flask_restx/api.html#Api.representation

    @api.response(404, 'Resource does not exist error')
    def get(self, set_code, notation):
        acceptType = request.headers.get('Accept')
        userFormat = request.args.get('format', None)
        mimetype, ldFormat = self._extractDesiredFormats(acceptType)

        # override the accept format if the user specifies a format
        if userFormat and userFormat in self.LD_TO_MIME_TYPE:
            ldFormat = userFormat
            mimetype = self.LD_TO_MIME_TYPE[userFormat]

        resp, status_code, headers = LODHandlerConcept(current_app.config).getConceptRDF(set_code, notation, ldFormat)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers
