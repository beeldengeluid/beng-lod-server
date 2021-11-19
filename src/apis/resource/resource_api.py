import logging
from flask import current_app, request, Response
from flask_restx import Namespace, Resource
from apis.mime_type_util import parse_accept_header, MimeType, get_profile_by_uri
import requests
from requests.exceptions import ConnectionError
from urllib.parse import urlparse, urlunparse
from util.APIUtil import APIUtil

api = Namespace('resource', description='Resources in RDF for Netherlands Institute for Sound and Vision.')


def get_lod_resource(level, identifier, mime_type, accept_profile, app_config):
    """ Generates the expected data based on the mime_type.
        :param level: meaning the catalogue type: 'program' (default), 'series', 'season', 'scene'.
        :param identifier: the DAAN id.
        :param mime_type: the mime_type, or serialization the resource is requested in.
        :param accept_profile: the profile (or model/schema/ontology) the data is requested in. \
            See: https://www.w3.org/TR/dx-prof-conneg/#related-http
            Example: Accept: application/ld+json; profile="http://schema.org"
        :param app_config: the application configuration
        :return: RDF data in a response object
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


def is_public_resource(resource_url):
    """ Checks whether the resource is allowed public access by firing a query to the public sparql endpoint.
    :param resource_url: the resource to be checked.
    :return True (yes, public access allowed), False (no, not allowed to dereference)
    """
    try:
        # get the SPARQL endpoint from the config
        sparql_endpoint = current_app.config.get('SPARQL_ENDPOINT')
        query_ask = 'ASK {<%s> ?p ?o . }' % resource_url

        # prepare and get the data from the triple store
        resp = requests.get(sparql_endpoint, params={'query': query_ask, 'format': 'json'})
        assert resp.status_code == 200, 'ASK request to sparql server was not successful.'

        return resp.json().get('boolean') is True

    except ConnectionError as e:
        app.logger.error(str(e))
    except AssertionError as e:
        app.logger.error(str(e))
    except Exception as e:
        app.logger.error(str(e))


def prepare_lod_resource_uri(level, identifier):
    """ Constructs valid url using the data domain, the level (cat type) and the identifier:
            {Beng data domain}/id/{cat_type}>/{identifier}
    :param level: the cat type
    :param identifier: the DAAN id
    :returns: a proper URI as it should be listed in the LOD server.
    """
    url_parts = urlparse(str(current_app.config.get('BENG_DATA_DOMAIN')))
    if url_parts.netloc is not None:
        path = '/'.join(['id', level, str(identifier)])
        parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
        return urlunparse(parts)
    else:
        return None


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/<any(program, series, season, scene):cat_type>/<int:identifier>', endpoint='dereference')
class ResourceAPI(Resource):

    def get(self, identifier, cat_type='program'):
        """ Get the RDF for the catalogue item. """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))
        lod_url = prepare_lod_resource_uri(cat_type, identifier)

        # only registered user can access all items
        auth_user = current_app.config.get('AUTH_USER')
        auth_pass = current_app.config.get('AUTH_PASSWORD')
        auth = request.authorization
        if auth is not None and auth.type == 'basic' and auth.username == auth_user and auth.password == auth_pass:
            # no restrictions, bypass the check
            logging.debug(request.authorization)
        else:
            # NOTE: this else clause is only there so we can download as lod-importer, but nobody else can.
            return APIUtil.toErrorResponse('access_denied', 'The resource can not be dereferenced.')
        # TODO: replace the else code with the code below in comment
        #     if not is_public_resource(resource_url=lod_url):
        #         return APIUtil.toErrorResponse('access_denied', 'The resource can not be dereferenced.')

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
