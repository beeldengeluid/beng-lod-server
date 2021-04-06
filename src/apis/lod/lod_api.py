from flask import current_app, request, Response, render_template
from flask_restx import Namespace, fields, Resource

from apis.lod.LODHandler import LODHandler
from apis.lod.LODHandlerConcept import LODHandlerConcept
# from apis.lod.LODSchemaHandler import LODSchemaHandler
from apis.lod.OpenDataLabHandler import OpenDataLabHandler
# from apis.lod.OpenDataLabHandler import OpenDataLabHandlerFlex

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
    #     @api.representation('application/rdf+xml','application/ld+json','text/turtle','text/n3')
    def get(self, level, identifier):
        acceptType = request.headers.get('Accept')
        userFormat = request.args.get('format', None)
        mimetype, ldFormat = self._extractDesiredFormats(acceptType)

        # override the accept format if the user specifies a format
        if userFormat and userFormat in self.LD_TO_MIME_TYPE:
            ldFormat = userFormat
            mimetype = self.LD_TO_MIME_TYPE[userFormat]

        resp, status_code, headers = LODHandler(current_app.config).getOAIRecord(level, identifier, ldFormat)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
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


@api.route('concept/<set_code>/<notation>', endpoint='concept')
class LODConceptAPI(Resource):
    MIME_TYPE_TO_LD = {
        'application/rdf+xml': 'xml',
        'application/ld+json': 'json-ld',
        'text/turtle': 'ttl',
        'text/n3': 'n3'
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

    @api.response(200, 'The requested concept in the right format.')
    @api.response(404, 'Resource does not exist.')
    # @api.doc('The resource is requested and a proper return message is generated.')
    def get(self, set_code, notation):
        accept_type = request.headers.get('Accept')
        user_format = request.args.get('format', None)
        mimetype, ld_format = self._extractDesiredFormats(accept_type)

        # override the accept format if the user specifies a format
        if user_format and user_format in self.LD_TO_MIME_TYPE:
            ld_format = user_format
            mimetype = self.LD_TO_MIME_TYPE[user_format]

        resp, status_code, headers = LODHandlerConcept(current_app.config).getConceptRDF(set_code, notation, ld_format)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


""" --------------------------- OPENDATALAB ENDPOINT -------------------------- """

MIMETYPE_XML = 'application/rdf+xml'
MIMETYPE_JSON_LD = 'application/ld+json'
MIMETYPE_TTL = 'text/turtle'


@api.route('media/<identifier>', endpoint='daan')
@api.doc(params={'identifier': 'An ID for a DAAN item. For example: "2101606230008608731"'})
class OpenDataLab(Resource):
    # TODO @api.route('media/<type>/<identifier>', endpoint='daan')

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

    @api.response(200, 'The requested media resource in the right format.')
    @api.response(404, 'Resource does not exist.')
    # TODO: define the resource not allowed for tenant items
    @api.doc(body='Get Media resources from NISV catalogue DAAN.')
    # @api.header('Accept', 'application/rdf+xml')
    # @api.header('Accept', 'application/ld+json')
    # @api.header('Accept', 'text/turtle')
    # @api.header('Accept', 'text/html')
    # NOTE: the header decorator can only be set once. The other values are discarded by openapi.
    # It also doesn effect the content-type dropdown in the swagger UI.
    def get(self, identifier):

        # TODO: fix the Content type in the OpenAPI UI
        # See: https://swagger.io/docs/specification/describing-responses/
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


# Unfortunately it is not allowed to use the flex datastore
# """ ------------------- OPEN DATA LAB endpoint using the flex datastore ----------------------------------------- """
#
#
# @api.route('media/<entry_type>/<identifier>', endpoint='daan_flexdatastore')
# @api.doc(params={'entry_type': "the type of the resource, e.g. either 'program', 'series', 'season' or 'scene_description'.",
#                  'identifier': 'An ID for a DAAN item. For example: "2101606230008608731"'}
#          )
# class OpenDataLabFlex(Resource):
#
#     MIME_TYPE_TO_LD = {
#         'application/rdf+xml': 'xml',
#         'application/ld+json': 'json-ld',
#         'text/turtle': 'ttl',
#     }
#
#     LD_TO_MIME_TYPE = {v: k for k, v in MIME_TYPE_TO_LD.items()}
#
#     def get_requested_format(self, accept_type):
#         mimetype = MIMETYPE_JSON_LD
#         if accept_type.find('rdf+xml') != -1:
#             mimetype = MIMETYPE_XML
#         elif accept_type.find('json+ld') != -1:
#             mimetype = MIMETYPE_JSON_LD
#         elif accept_type.find('json') != -1:
#             mimetype = MIMETYPE_JSON_LD
#         elif accept_type.find('turtle') != -1:
#             mimetype = MIMETYPE_TTL
#         return mimetype, self.MIME_TYPE_TO_LD[mimetype]
#
#     @api.response(200, 'The requested media resource in the right format.')
#     @api.response(404, 'Resource does not exist.')
#     @api.doc('Get Media resources from NISV catalogue DAAN')
#     def get(self, entry_type, identifier):
#
#         # TODO: fix the Accept type in the OpenAPI UI
#         accept_type = request.headers.get('Accept')
#
#         # "you can pass either a mime-type or the name (a list of available parsers is available)"
#         mimetype, ld_format = self.get_requested_format(accept_type)
#         resp, status_code, headers = \
#             OpenDataLabHandlerFlex(current_app.config).get_media_item_nisv(uri=identifier,
#                                                                            resource_type=entry_type,
#                                                                            ld_format=ld_format)
#         # make sure to apply the correct mimetype for valid responses
#         if headers is None:
#             headers = {'Content-Type': mimetype}
#         else:
#             headers['Content-Type'] = mimetype
#         if status_code == 200:
#             return Response(resp, mimetype=mimetype, headers=headers)
#             # return Response(resp, mimetype=mimetype, headers=request.headers)
#
#         # otherwise resp SHOULD be a json error message and thus the response can be returned like this
#         return resp, status_code, headers
