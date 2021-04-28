from flask import current_app, request, Response
from flask_restx import Namespace, fields, Resource
from flask_accept import accept

from apis.lod.DAANStorageLODHandler import DAANStorageLODHandler
from apis.lod.LODHandlerConcept import LODHandlerConcept

api = Namespace('lod', description='Resources in RDF for Netherlands Institute for Sound and Vision.')

# generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- RESOURCE ENDPOINT -------------------------- """

MIME_TYPE_TO_LD = {
    'application/rdf+xml': 'xml',
    'application/json+ld': 'json-ld',
    'application/n-triples': 'nt',
    'text/turtle': 'ttl',
}


def get_generic(level, identifier):
    """ Experimental function that generates the expected data based on the mime_type.
        It can be used by the accept-decorated methods from the resource derived class.
    """
    # Note that the rdflib-json-ld plugin doesn't accept mime_type, therefore we use a small converter
    # TODO: officially, the mimetype is 'application/ld+json'
    mime_type = request.headers.get('Accept', default='application/json+ld')

    ld_format = MIME_TYPE_TO_LD.get(mime_type)

    # TODO: check the Accept header for the key/value 'profile'. What value?
    # sdo = False
    # if sdo is True:
    #     resp, status_code, headers = SDOStorageLODHandler(current_app.config).getStorageRecord(level,
    #                                                                                             identifier,
    #                                                                                             ld_format)

    resp, status_code, headers = DAANStorageLODHandler(current_app.config).getStorageRecord(level,
                                                                                            identifier,
                                                                                            ld_format)
    # make sure to apply the correct mimetype for valid responses
    if status_code == 200:
        return Response(resp, mimetype=mime_type, headers=headers)

    return Response(resp, status_code, headers=headers)


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('resource/<level>/<identifier>', endpoint='dereference')
class LODAPI(Resource):

    # TODO: add the profile into the Accept header. See: https://www.w3.org/TR/dx-prof-conneg/
    # TODO: officially, the mimetype is 'application/ld+json'
    @accept('application/json+ld')
    def get(self, level, identifier):
        return get_generic(level, identifier)

    @get.support('application/rdf+xml')
    def get_rdf_xml(self, level, identifier):
        return get_generic(level, identifier)

    @get.support('application/n-triples')
    def get_n_triples(self, level, identifier):
        return get_generic(level, identifier)

    @get.support('text/turtle')
    def get_turtle(self, level, identifier):
        return get_generic(level, identifier)

    @get.support('text/html')
    def get_html(self, level, identifier):
        return get_generic(level, identifier)


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
