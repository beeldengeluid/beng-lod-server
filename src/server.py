import logging

from flask import Flask, request, Response, send_from_directory, redirect, render_template
from flask_cors import CORS
import os
from apis import api
#from ontodoc import ontodoc
from SchemaInMemory import SchemaInMemory
from util.APIUtil import APIUtil
from cache import cache


app = Flask(__name__)

# init the config
app.config.from_object('config.settings.Config')
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['RESTPLUS_VALIDATE'] = False

app.debug = app.config['DEBUG']

CORS(app)

cache.init_app(app)


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
            p['sim'] = SchemaInMemory(profile=p)


def get_profile_dir(profile):
    return 'static/ontospy/{}'.format(profile['prefix']) if 'prefix' in profile else None


"""
def generate_ontospy_html(profile):
    if 'schema' in profile and 'prefix' in profile:
        profile_dir = get_profile_dir(profile)
        if profile_dir and not os.path.exists(profile_dir):
            print('Generating ontospy HTML for {}'.format(profile['prefix']))
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
    return send_from_directory(get_profile_dir(active_profile), 'index.html')


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
    elif 'text/html' in request.headers.get('Accept') and path.find('.') == -1:
        html_path = active_profile['sim'].resource_name_to_html(  # make sure load the correct html template
            app.config['ACTIVE_PROFILE']['prefix'],
            app.config['ACTIVE_PROFILE']['uri'],
            path
        )
        if html_path:
            return send_from_directory(get_profile_dir(active_profile), html_path)
    elif os.path.exists(os.path.join(get_profile_dir(active_profile), path)):
        if path.find('.html') != -1:  # redirect the html to the nice Resource URI
            resource_name = active_profile['sim'].url_path_to_resource_name(active_profile['prefix'], path)
            if resource_name:
                return redirect('/schema/{}'.format(resource_name))
        return send_from_directory(get_profile_dir(active_profile), path)
    return Response('This page does not exist (404)')


@app.route('/yasgui')
@app.route('/yasgui/')
def yasgui():
    """ Return a UI where SPARQL examples can be loaded.
    GH issue # 136
    """
    import json

    def read_example_queries(fn='example_queries.json'):
        """ Load queries from a JSON document."""
        with open(fn, 'r') as f:
            return json.load(f, strict=False)

    queries = {}
    example_fn = app.config.get('SPARQL_EXAMPLES')
    if os.path.exists(example_fn):
        queries = read_example_queries(fn=example_fn)
    return render_template('sparql_ui_with_examples.html', my_examples=queries.get('examples'))


if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
