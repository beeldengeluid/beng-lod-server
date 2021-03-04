from flask import current_app, request, Response, render_template
from flask_restx import Namespace, fields, Resource

from apis.lod.LODHandler import LODHandler
from apis.lod.LODHandlerConcept import LODHandlerConcept
# from apis.lod.LODSchemaHandler import LODSchemaHandler
from apis.lod.OpenDataLabHandler import OpenDataLabHandler

api = Namespace('ODL', description='Linked Open Data at NISV')

# generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- RESOURCE ENDPOINT -------------------------- """


@api.route('resource/<level>/<identifier>', endpoint='dereference')
class LODAPI(Resource):

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

    @api.response(404, 'Resource does not exist error')
#     @api.representation('application/rdf+xml','application/ld+json','text/turtle','text/n3')
    def get(self, level, identifier):
        acceptType = request.headers.get('Accept')
        userFormat = request.args.get('format', None)
        mimetype, ldFormat = self._extractDesiredFormats(acceptType)

        #override the accept format if the user specifies a format
        if userFormat and userFormat in self.LD_TO_MIME_TYPE:
            ldFormat = userFormat
            mimetype = self.LD_TO_MIME_TYPE[userFormat]

        resp, status_code, headers = LODHandler(current_app.config).getOAIRecord(level, identifier, ldFormat)

        #make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        #otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


# """ --------------------------- SCHEMA ENDPOINT -------------------------- """
#
#
# # # @api.route('schema', endpoint='schema')
# # @api.route('schema/<class_or_property>', endpoint='schema')
#
# @api.route('schema')
# @api.route('schema/', endpoint='schema')
# class LODSchemaAPI(Resource):
#
#     @api.response(404, 'Schema does not exist error')
#     def get(self):
#         resp, status_code, headers = LODSchemaHandler(current_app.config).getSchema()
#         if status_code == 200:
#             return Response(resp, mimetype='text/turtle')
#         return resp, status_code, headers


""" --------------------------- GTAA ENDPOINT -------------------------- """


@api.route('concept/<set>/<notation>', endpoint='concept')
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

    @api.response(404, 'Resource does not exist error')
    def get(self, set, notation):
        acceptType = request.headers.get('Accept')
        userFormat = request.args.get('format', None)
        mimetype, ldFormat = self._extractDesiredFormats(acceptType)

        #override the accept format if the user specifies a format
        if userFormat and userFormat in self.LD_TO_MIME_TYPE:
            ldFormat = userFormat
            mimetype = self.LD_TO_MIME_TYPE[userFormat]

        resp, status_code, headers = LODHandlerConcept(current_app.config).getConceptRDF(set, notation, ldFormat)

        #make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        #otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


""" --------------------------- OPENDATALAB ENDPOINT -------------------------- """

MIMETYPE_XML = 'application/rdf+xml'
MIMETYPE_JSON_LD = 'application/ld+json'
MIMETYPE_TTL = 'text/turtle'


@api.route('media/<identifier>', endpoint='daan')
@api.doc(params={'identifier': 'An ID for a DAAN item. For example: "2101608170160873531"'})
class OpenDataLab(Resource):

    MIME_TYPE_TO_LD = {
        'application/rdf+xml': 'xml',
        'application/ld+json': 'json-ld',
        'text/turtle': 'ttl',
    }

    LD_TO_MIME_TYPE = {v: k for k, v in MIME_TYPE_TO_LD.items()}

    def get_requested_format(self, accept_type):
        mimetype = MIMETYPE_JSON_LD
        if accept_type.find('rdf+xml') != -1:
            mimetype = MIMETYPE_XML
        elif accept_type.find('json+ld') != -1:
            mimetype = MIMETYPE_JSON_LD
        elif accept_type.find('json') != -1:
            mimetype = MIMETYPE_JSON_LD
        elif accept_type.find('turtle') != -1:
            mimetype = MIMETYPE_TTL
        return mimetype, self.MIME_TYPE_TO_LD[mimetype]

    @api.response(404, 'Resource does not exist error')
    @api.doc('Get Media resources from NISV catalogue DAAN')
    def get(self, identifier):
        # TODO: fix the Accept type in the OpenAPI UI
        accept_type = request.headers.get('Accept')

        # "you can pass either a mime-type or the name (a list of available parsers is available)"
        mimetype, ld_format = self.get_requested_format(accept_type)
        resp, status_code, headers = OpenDataLabHandler(current_app.config).get_media_item_nisv(uri=identifier,
                                                                                                ld_format=ld_format)

        # make sure to apply the correct mimetype for valid responses
        if headers is None:
            headers = {'Content-Type': mimetype}
        else:
            headers['Content-Type'] = mimetype
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)
            # return Response(resp, mimetype=mimetype, headers=request.headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers
