from flask import Flask, request, Response, send_from_directory, redirect
from flask_cors import CORS
import os
from apis import api
from SchemaInMemory import SchemaInMemory
from util.APIUtil import APIUtil
from util.base_util import init_logger, validate_config
#from ontodoc import ontodoc

app = Flask(__name__)

# init the config
app.config.from_object('config.settings.Config')
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['RESTPLUS_VALIDATE'] = False

logger = init_logger(app)

if not validate_config(app.config):
    logger.error('Invalid config, quitting')
    quit()

app.debug = app.config['DEBUG']

CORS(app)

def get_active_profile():
    def_profile = app.config['PROFILES'][0]
    for p in app.config['PROFILES']:
        if 'default' in p and p['default'] is True:
            def_profile = p
            break
    return def_profile


# TODO now the active profile is static and cannot be defined via the URL
app.config['ACTIVE_PROFILE'] = get_active_profile()


# Code added to generate the ontology documentation
@app.before_first_request
def server_init():
    loaded_schemas = {}
    for p in app.config['PROFILES']:
        if 'prefix' in p and 'schema' in p and p['schema']:
            # generate the ontospy HTML for the configured profile
            #generate_ontospy_html(p)
            # schema in memory
            logger.debug(f"Loading profile {p['prefix']} in memory")
            p['sim'] = SchemaInMemory(profile=p)

"""
def get_ontospy_dir(profile):
    return 'static/ontospy/{}'.format(profile['prefix']) if 'prefix' in profile else None

def generate_ontospy_html(profile):
    if 'schema' in profile and 'prefix' in profile:
        profile_dir = get_ontospy_dir(profile)
        if profile_dir and not os.path.exists(profile_dir):
            logger.debug('Generating ontospy HTML for {}'.format(profile['prefix']))
            ontodoc(ontology_file=profile['schema'], output_path=profile_dir, profile=profile)
"""

api.init_app(
    app,
    title='Open Data Lab API - Netherlands Institute for Sound and Vision',
    description='Get RDF for open datasets and for resources in the NISV catalogue.')

"""------------------------------------------------------------------------------
PING / HEARTBEAT ENDPOINT
------------------------------------------------------------------------------"""


@app.route('/ping')
def ping():
    logger.debug('Received ping')
    return Response('pong', mimetype='text/plain')


"""------------------------------------------------------------------------------
ROUTING FOR BROWSING THE SCHEMAS/PROFILES (TODO INTEGRATE WITH SWAGGER API)
------------------------------------------------------------------------------"""


@app.route('/schema')
@app.route('/schema/')
def schema():
    active_profile = app.config['ACTIVE_PROFILE']

    if 'text/turtle' in request.headers.get('Accept'):
        # a text page with the RDF in turtle format is returned.
        if os.path.exists(app.config['ACTIVE_PROFILE']['schema']):
            f = open(app.config['ACTIVE_PROFILE']['schema'], 'r')
            schema_ttl = f.read()
            f.close()
            return APIUtil.toSuccessResponse(schema_ttl)
        return APIUtil.toErrorResponse('internal_server_error', 'The schema file could not be found')
    #return send_from_directory(get_ontospy_dir(active_profile), 'index.html')
    return APIUtil.toErrorResponse('not_found', 'This page does not exist (anymore)')

@app.route('/schema/<path:path>')
def schema_path(path=None):
    active_profile = app.config['ACTIVE_PROFILE']

    if 'text/turtle' in request.headers.get('Accept'):
        # a text page with the RDF for the resource represented in the turtle format is returned.
        uri = "http://data.rdlabs.beeldengeluid.nl/schema/%s" % path
        return active_profile['sim'].get_resource(class_or_prop=uri)
    elif 'application/rdf+xml' in request.headers.get('Accept'):
        # an XML page with the RDF for the resource represented in RDF/XML format is returned.
        uri = "http://data.rdlabs.beeldengeluid.nl/schema/%s" % path
        return active_profile['sim'].get_resource(class_or_prop=uri, return_format='xml')
    # elif 'application/ld+json' in request.headers.get('Accept'):
    #     # an page with the RDF for the resource represented in JSON-LD format is returned.
    #     uri = "http://data.rdlabs.beeldengeluid.nl/schema/%s" % path
    #     return active_profile['sim'].get_resource(class_or_prop=uri, return_format='json+ld')

    """
    elif 'text/html' in request.headers.get('Accept') and path.find('.') == -1:
        html_path = active_profile['sim'].resource_name_to_html(  # make sure load the correct html template
            app.config['ACTIVE_PROFILE']['prefix'],
            app.config['ACTIVE_PROFILE']['uri'],
            path
        )
        if html_path:
            return send_from_directory(get_ontospy_dir(active_profile), html_path)
    elif os.path.exists(os.path.join(get_ontospy_dir(active_profile), path)):
        if path.find('.html') != -1:  # redirect the html to the nice Resource URI
            resource_name = active_profile['sim'].url_path_to_resource_name(active_profile['prefix'], path)
            if resource_name:
                return redirect('/schema/{}'.format(resource_name))
        return send_from_directory(get_ontospy_dir(active_profile), path)
    """
    return APIUtil.toErrorResponse('not_found', 'This page does not exist (anymore)')


if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
