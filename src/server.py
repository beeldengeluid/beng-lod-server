from flask import Flask, render_template, request, Response, send_from_directory, redirect
from flask_cors import CORS
from datetime import datetime
import os
from pathlib import Path
from apis import api
from ontodoc import ontodoc
from SchemaInMemory import SchemaInMemory
from util.APIUtil import APIUtil

app = Flask(__name__)

# init the config
app.config.from_object('settings.Config')
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['RESTPLUS_VALIDATE'] = False

app.debug = app.config['DEBUG']

CORS(app)


# Code added to generate the ontology documentation
@app.before_first_request
def server_init():
    output_path = 'schema'
    if not os.path.exists(os.path.join(Path(app.static_folder).parent, output_path)):
        ontodoc(ontology_file=app.config['SCHEMA_FILE'], output_path=output_path)


# schema in memory
sim = SchemaInMemory(schema_file=app.config['SCHEMA_FILE'])


# print(Path(app.static_folder).parent)

api.init_app(
    app,
    title='Open Data Lab - Beeld en Geluid',
    description='Open Data available at the Netherlands Institute for Sound and Vision.')

"""------------------------------------------------------------------------------
CUSTOM TEMPLATE FUNCTIONS
------------------------------------------------------------------------------"""


# Formats dates to be used in templates
@app.template_filter()
def datetime_format(value, dt_format='%d, %b %Y'):
    return datetime.strptime(value, format="%Y-%m-%dT%H:%M:%SZ").strftime(dt_format)


@app.template_filter()
def getLastStringAfter(value):
    last_index = value.rindex("/")
    return value[last_index + 1:len(value)]


@app.template_filter()
def externalResource(url):
    beng_schema = "http://data.rdlabs.beeldengeluid.nl"
    if url.find(beng_schema) == -1:
        return True
    else:
        return False


"""------------------------------------------------------------------------------
PING / HEARTBEAT ENDPOINT
------------------------------------------------------------------------------"""


@app.route('/ping')
def ping():
    return Response('pong', mimetype='text/plain')


"""------------------------------------------------------------------------------
REGULAR ROUTING (STATIC CONTENT)
------------------------------------------------------------------------------"""


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/schema/')
def schema():
    if 'text/turtle' in request.headers.get('Accept'):
        # a text page with the RDF in turtle format is returned.
        if os.path.exists(app.config['SCHEMA_FILE']):
            f = open(app.config['SCHEMA_FILE'], 'r')
            schema_ttl = f.read()
            f.close()
            return APIUtil.toSuccessResponse(schema_ttl)
        return APIUtil.toErrorResponse('internal_server_error', 'The schema file could not be found')
    return send_from_directory(os.path.join(Path(app.static_folder).parent, 'schema'), 'index.html')


@app.route('/schema/static/libs/bootswatch3_2/yeti/fonts/<path:path>')
def schema_fonts_path(path):
    return send_from_directory('schema/static/libs/bootstrap-3_3_7-dist/fonts', path)


@app.route('/schema/static/<path:path>')
def schema_static(path):
    return send_from_directory('schema/static', path)


@app.route('/schema/<path:path>')
def schema_path(path):
    print(request.path)
    rp = request.path
    if rp != '/' and rp.endswith('/'):
        return redirect(rp[:-1])
    elif rp.endswith('.html'):
        # HTML representation pages for the resource is served, but URI name is shown (preferred path).
        # e.g. "http://data.rdlabs.beeldengeluid.nl/schema/Person" is requested and shown in the address bar, but
        # the HTML page '/schema/class-nisvperson.html' is served.
        if path.startswith('class-nisv'):
            entity_name = path[10:-5]
            resource_name = sim.get_resource_name(entity_name=entity_name)
            return redirect('/schema/%s' % resource_name)
        elif path.startswith('prop-nisv'):
            entity_name = path[9:-5]
            resource_name = sim.get_resource_name(entity_name=entity_name, resource_type='prop')
            return redirect('/schema/%s' % resource_name)
        return send_from_directory(os.path.join(Path(app.static_folder).parent, 'schema'), path)
    elif 'text/turtle' in request.headers.get('Accept'):
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
    # not supported yet

    else:
        # Returned pages are either class or prop pages generated by ontospy. Note that the requested page names
        # in the address bar can be replaced with the preferred resource names.
        # E.g. 'http://localhost:5309/schema/prop-nisvhascarrierannotation.html' is requested and returned,
        # but the address bar shows 'http://localhost:5309/schema/hasCarrierAnnotation'.
        # The request is redirected and the console will show something like this:
        # "GET /schema/prop-nisvhascarrierannotation.html HTTP/1.1" 302 -
        # "GET /schema/hasCarrierAnnotation HTTP/1.1" 200 -
        doc_title = 'class-nisv%s.html' % path.lower()
        if os.path.exists(os.path.join(Path(app.static_folder).parent, 'schema/%s' % doc_title)):
            return send_from_directory('schema', doc_title)
        else:
            doc_title = 'prop-nisv%s.html' % path.lower()
            return send_from_directory('schema', doc_title)


if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
