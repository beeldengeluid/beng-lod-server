from flask import current_app, request, Response
from flask_restx import Namespace, fields, Resource
from flask_accept import accept
from apis.lod.DAANStorageLODHandler import DAANStorageLODHandler
from apis.lod.SDOStorageLODHandler import SDOStorageLODHandler
from apis.lod.LODHandlerConcept import LODHandlerConcept

api = Namespace('lod', description='Resources in RDF for Netherlands Institute for Sound and Vision.')

# generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- RESOURCE ENDPOINT -------------------------- """

MIME_TYPE_JSON_LD = 'application/ld+json'
MIME_TYPE_RDF_XML = 'application/rdf+xml'
MIME_TYPE_TURTLE = 'text/turtle'
MIME_TYPE_N_TRIPLES = 'application/n-triples'
MIME_TYPE_JSON = 'application/json'

MIME_TYPE_TO_LD = {
    MIME_TYPE_RDF_XML: 'xml',
    MIME_TYPE_JSON_LD: 'json-ld',
    MIME_TYPE_N_TRIPLES: 'nt',
    MIME_TYPE_TURTLE: 'ttl',
    MIME_TYPE_JSON: 'json-ld'
}

# TODO: make sure the schema file is downloadable in turtle
NISV_PROFILE = 'http://data.rdlabs.beeldengeluid.nl/schema'
SDO_PROFILE = "http://schema.org"


def get_generic(level, identifier):
    """ Experimental function that generates the expected data based on the mime_type.
        It can be used by the accept-decorated methods from the resource derived class.

        :param: data: one of three params that is here for content-type to be visible in the UI.
        :param: code: status_code. also one of the three params for UI
        :param: headers: one of the params for the OpenAPI UI as well.
        :param: level, meaning the catalogue type, e.g. like 'program' (default), 'series', etc.
        :param: identifier, the DAAN id the resource is findable with, in combination with level
    """
    # TODO: check if the rdflib-json-ld plugin does accept mime_type='application/ld+json'

    """ See: https://www.w3.org/TR/dx-prof-conneg/#related-http
        profile = request.headers.get('Accept-Profile', default=NISV_PROFILE)
        NOTE: Accept-Profile and Content-Profile are not really adopted yet. Therefore (ab-)use the
        Accept header with additional parameter:
        Example: Accept: application/ld+json; profile="http://schema.org"
    """
    accept_parts = request.headers.get('Accept').split(';')
    accept_profile = NISV_PROFILE
    mime_type = MIME_TYPE_JSON_LD
    if len(accept_parts) == 1:
        mime_type = request.headers.get('Accept')
    if len(accept_parts) > 1:
        for part in accept_parts:
            kv = part.split('=')
            if len(kv) > 1 and kv[0] == 'profile':
                accept_profile = kv[1]

    # mime_type = request.headers.get('Accept', default=MIME_TYPE_JSON_LD)
    ld_format = MIME_TYPE_TO_LD.get(mime_type)
    if accept_profile == SDO_PROFILE:
        resp, status_code, headers = SDOStorageLODHandler(current_app.config).get_storage_record(level,
                                                                                                 identifier,
                                                                                                 ld_format)
        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            profile_param = '='.join(['profile', SDO_PROFILE])
            content_type = ';'.join([headers['Content-Type'], profile_param])
            headers['Content-Type'] = content_type
            return Response(resp, mimetype=mime_type, headers=headers)
        return Response(resp, status_code, headers=headers)
    else:
        resp, status_code, headers = DAANStorageLODHandler(current_app.config).get_storage_record(level,
                                                                                                  identifier,
                                                                                                  ld_format)
        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            profile_param = '='.join(['profile', NISV_PROFILE])
            content_type = ';'.join([headers['Content-Type'], profile_param])
            headers['Content-Type'] = content_type
            return Response(resp, mimetype=mime_type, headers=headers)
        return Response(resp, status_code, headers=headers)


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('resource/<any(program, series, season, logtrackitem):level>/<int:identifier>', endpoint='dereference')
class LODAPI(Resource):

    # TODO: add the profile into the Accept header. See: https://www.w3.org/TR/dx-prof-conneg/
    @accept('application/ld+json')
    def get(self, identifier, level='program'):
        # note we need to use empty params for the UI
        return get_generic(level=level, identifier=identifier)

    @get.support('application/rdf+xml')
    def get_rdf_xml(self, identifier, level='program'):
        return get_generic(level=level, identifier=identifier)

    @get.support('application/n-triples')
    def get_n_triples(self, identifier, level='program'):
        return get_generic(level=level, identifier=identifier)

    @get.support('text/turtle')
    def get_turtle(self, identifier, level='program'):
        return get_generic(level=level, identifier=identifier)

    @get.support('text/html')
    def get_html(self, identifier, level='program'):
        return get_generic(level=level, identifier=identifier)

    @get.support('application/json')
    def get_json(self, identifier, level='program'):
        return get_generic(level=level, identifier=identifier)


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

    @api.response(404, 'Resource does not exist error')
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
