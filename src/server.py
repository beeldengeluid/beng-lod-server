from flask import Flask, render_template, request, Response, send_from_directory, redirect
from flask_cors import CORS
import datetime
from datetime import datetime
import os
from pathlib import Path
from apis import api
from ontodoc import ontodoc
from SchemaInMemory import SchemaInMemory
from util.APIUtil import APIUtil
from cache import cache
from jinja2.exceptions import TemplateNotFound

app = Flask(__name__)

# init the config
app.config.from_object('settings.Config')
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['RESTPLUS_VALIDATE'] = False
#app.config['CACHE_TYPE'] = "SimpleCache"

app.debug = app.config['DEBUG']

CORS(app)

cache.init_app(app)

def get_default_profile():
    def_profile = app.config['PROFILES'][0]
    for p in app.config['PROFILES']:
        if 'default' in p and p['default'] == True:
            def_profile = p
            break
    return def_profile

app.config['DEFAULT_PROFILE'] = get_default_profile()

# Code added to generate the ontology documentation
@app.before_first_request
def server_init():
    #ontospy_output_dir = os.path.join(Path(app.static_folder).parent, app.config['ONTOSPY_OUTPUT_DIR'])
    if not os.path.exists(app.config['ONTOSPY_OUTPUT_DIR']):
        ontodoc(ontology_file=app.config['DEFAULT_PROFILE']['schema'], output_path=app.config['ONTOSPY_OUTPUT_DIR'])


# schema in memory
sim = SchemaInMemory(schema_file=app.config['DEFAULT_PROFILE']['schema'])

api.init_app(
    app,
    title='Open Data Lab API - Nederlands Instituut voor Beeld en Geluid',
    description='Get RDF for resources in the DAAN catalogue and the GTAA thesaurus.')

"""------------------------------------------------------------------------------
PING / HEARTBEAT ENDPOINT
------------------------------------------------------------------------------"""

@app.route('/ping')
def ping():
    return Response('pong', mimetype='text/plain')


"""------------------------------------------------------------------------------
REGULAR ROUTING (STATIC CONTENT)
------------------------------------------------------------------------------"""

@app.route('/schema')
@app.route('/schema/')
def schema():
    if 'text/turtle' in request.headers.get('Accept'):
        # a text page with the RDF in turtle format is returned.
        if os.path.exists(app.config['DEFAULT_PROFILE']['schema']):
            f = open(app.config['DEFAULT_PROFILE']['schema'], 'r')
            schema_ttl = f.read()
            f.close()
            return APIUtil.toSuccessResponse(schema_ttl)
        return APIUtil.toErrorResponse('internal_server_error', 'The schema file could not be found')
    return send_from_directory(app.config['ONTOSPY_OUTPUT_DIR'], 'index.html')

@app.route('/schema/<path:path>')
def schema_path(path=None):
    print('path: {}'.format(path))
    if 'text/turtle' in request.headers.get('Accept'):
        # a text page with the RDF for the resource represented in the turtle format is returned.
        uri = "http://data.rdlabs.beeldengeluid.nl/schema/%s" % path
        return sim.get_resource(class_or_prop=uri)
    elif 'application/rdf+xml' in request.headers.get('Accept'):
        # an XML page with the RDF for the resource represented in RDF/XML format is returned.
        uri = "http://data.rdlabs.beeldengeluid.nl/schema/%s" % path
        return sim.get_resource(class_or_prop=uri, return_format='xml')
    # elif 'application/ld+json' in request.headers.get('Accept'):
    #     # an page with the RDF for the resource represented in JSON-LD format is returned.
    #     uri = "http://data.rdlabs.beeldengeluid.nl/schema/%s" % path
    #     return sim.get_resource(class_or_prop=uri, return_format='json+ld')
    elif 'text/html' in request.headers.get('Accept') and path.find('.') == -1:
        html_path = sim.resource_name_to_html( #make sure load the correct html template
            app.config['DEFAULT_PROFILE']['id'],
            path
        )
        if html_path:
            return send_from_directory(app.config['ONTOSPY_OUTPUT_DIR'], html_path)
    elif os.path.exists(os.path.join(app.config['ONTOSPY_OUTPUT_DIR'], path)):
        if path.find('.html') != -1: #redirect the html to the nice Resource URI
            resource_name = sim.url_path_to_resource_name(path)
            if resource_name:
                return redirect('/schema/{}'.format(resource_name))
        return send_from_directory(app.config['ONTOSPY_OUTPUT_DIR'], path)
    return Response('This page does not exist (404)')

if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
