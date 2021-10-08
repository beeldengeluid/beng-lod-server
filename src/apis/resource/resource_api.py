from flask import current_app, request, Response
from flask_restx import Namespace, fields, Resource
from apis.mime_type_util import parse_accept_header, MimeType, get_profile_by_uri

api = Namespace('resource', description='Resources in RDF for Netherlands Institute for Sound and Vision.')

def get_lod_resource(level, identifier, mime_type, accept_profile, app_config):
    """ Generates the expected data based on the mime_type.
        It can be used by the accept-decorated methods from the resource derived class.

        :param level: meaning the catalogue type, e.g. like 'program' (default), 'series', etc.
        :param identifier: the DAAN id the resource is findable with, in combination with level
        :param mime_type: the mime_type, or serialization the resource is requested in.
        :param accept_profile: the model/schema/ontology the data is requested in.
        :param app_config: the application configuration
        :return: RDF data in a response object
    """
    """ See: https://www.w3.org/TR/dx-prof-conneg/#related-http
        NOTE: Abuse the Accept header with additional parameter:
        Example: Accept: application/ld+json; profile="http://schema.org"
    """
    mt = None
    try:
        mt = MimeType(mime_type)
    except ValueError as e:
        mt = MimeType.JSON_LD

    profile = get_profile_by_uri(accept_profile, app_config)

    resp, status_code, headers = profile['storage_handler'](app_config, profile).get_storage_record(
        level,
        identifier,
        mt.to_ld_format()
    )
    # make sure to apply the correct mimetype for valid responses
    if status_code == 200:
        content_type = mt.value
        if headers.get('Content-Type') is not None:
            content_type = headers.get('Content-Type')
        profile_param = '='.join(['profile', '"{}"'.format(profile['schema'])])
        headers['Content-Type'] = ';'.join([content_type, profile_param])
        return Response(resp, mimetype=mt.value, headers=headers)
    return Response(resp, status_code, headers=headers)

@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/<any(program, series, season, logtrackitem):cat_type>/<int:identifier>', endpoint='dereference')
class ResourceAPI(Resource):

    def get(self, identifier, cat_type='program'):
        """ Get the RDF for the catalogue item. """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))

        if mime_type:
            # note we need to use empty params for the UI
            return get_lod_resource(
                level=cat_type,
                identifier=identifier,
                mime_type=mime_type,
                accept_profile=accept_profile,
                app_config=current_app.config
            )
        return Response('Error: No mime type detected...')