from flask import current_app, request, Response
from flask_restx import Namespace, fields, Resource
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
# DAAN_PROFILE = 'http://data.rdlabs.beeldengeluid.nl/schema/'
# SDO_PROFILE = 'https://schema.org/'

def get_profile_by_uri(profile_uri, app_config):
    print('looking for: {}'.format(profile_uri))
    for p in app_config['PROFILES']:
        if p['uri'] == profile_uri:
            print('ACTUALLY GOT THE PROFILE: {}'.format(profile_uri))
            return p
    else:  # otherwise return the default profile
        return app_config['ACTIVE_PROFILE']


""" Generates the expected data based on the mime_type.
    It can be used by the accept-decorated methods from the resource derived class.

    :param: level, meaning the catalogue type, e.g. like 'program' (default), 'series', etc.
    :param: identifier, the DAAN id the resource is findable with, in combination with level
"""
""" See: https://www.w3.org/TR/dx-prof-conneg/#related-http
    NOTE: Abuse the Accept header with additional parameter:
    Example: Accept: application/ld+json; profile="http://schema.org"
"""


def get_lod_resource(level, identifier, mime_type, accept_profile, app_config):
    profile = get_profile_by_uri(accept_profile, app_config)

    # TODO: check if the rdflib-json-ld plugin does accept mime_type='application/ld+json'
    ld_format = MIME_TYPE_TO_LD.get(mime_type)

    print('MIMETYPE {} LD FORMAT {}'.format(mime_type, ld_format))

    resp, status_code, headers = profile['storage_handler'](app_config, profile).get_storage_record(
        level,
        identifier,
        ld_format
    )
    # make sure to apply the correct mimetype for valid responses
    if status_code == 200:
        content_type = mime_type
        if headers.get('Content-Type') is not None:
            content_type = headers.get('Content-Type')
        profile_param = '='.join(['profile', '"{}"'.format(profile['schema'])])
        headers['Content-Type'] = ';'.join([content_type, profile_param])
        return Response(resp, mimetype=mime_type, headers=headers)
    return Response(resp, status_code, headers=headers)


def parse_accept(accept_header):
    """ Parses an Accept header for a request for RDF to the server. It returns the mimet_type and profile.
    :param: accept_header: the Accept parameter from the HTTP request.
    :returns: mime_type, accept_profile. None if input parameter is missing.
    """
    print(accept_header)
    mime_type = MIME_TYPE_JSON_LD
    accept_profile = None

    if accept_header is None or accept_header == '*/*':
        return mime_type, accept_profile

    accept_parts = accept_header.split(';')

    print(accept_parts)
    if len(accept_parts) == 1:
        mime_type = request.headers.get('Accept')
        # # uncomment if you want to enforce a profile (for testing)
        # profile_param = '='.join(['profile', '"{}"'.format(SDO_PROFILE)])
        # accept_parts.append(profile_param)
    if len(accept_parts) > 1:
        for part in accept_parts:
            kv = part.split('=')
            if len(kv) > 1 and kv[0] == 'profile':
                accept_profile = kv[1].replace('"', '')
    return mime_type, accept_profile


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('resource/<any(program, series, season, logtrackitem):level>/<int:identifier>', endpoint='dereference')
class LODAPI(Resource):

    # @accept('application/ld+json')
    def get(self, identifier, level='program'):
        mime_type, accept_profile = parse_accept(request.headers.get('Accept'))

        if mime_type:
            # note we need to use empty params for the UI
            return get_lod_resource(
                level=level,
                identifier=identifier,
                mime_type=mime_type,
                accept_profile=accept_profile,
                app_config=current_app.config
            )
        return Response('Error: No mime type detected...')


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

        resp, status_code, headers = LODHandlerConcept(current_app.config).get_concept_rdf(set_code, notation,
                                                                                           ld_format)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers
