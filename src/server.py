from flask import Flask, render_template, request, Response, url_for, send_from_directory, redirect
from flask_cors import CORS
import json
import datetime
import os
from pathlib import Path
from apis import api
from ontodoc import ontodoc

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
    #ontodoc(ontology_file=app.config['SCHEMA_FILE'])
    print('Willem: deze wordt bij de eerste request naar de server gedraaid: check dan ook even of de dir all bestaat, zodat niet onnodig die docs worden gegenereerd')

print(Path(app.static_folder).parent)

api.init_app(
    app,
    title='Beeld en Geluid LOD API',
    description='LOD API mostly for e.g. dereferencing B&G resources')

"""------------------------------------------------------------------------------
CUSTOM TEMPLATE FUNCTIONS
------------------------------------------------------------------------------"""

# Formats dates to be used in templates
@app.template_filter()
def datetimeformat(value, format='%d, %b %Y'):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime(format)


@app.template_filter()
def getLastStringAfter(value):
    lastIndex = value.rindex("/")
    return value[lastIndex + 1:len(value)]


@app.template_filter()
def externalResource(url):
    BENGSCHEMA = "http://data.rdlabs.beeldengeluid.nl"
    if url.find(BENGSCHEMA) == -1:
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


@app.route('/html-schema', methods=['GET'])
@app.route('/html-schema/', methods=['GET'])
@app.route('/html-schema/<string:language>/')
@app.route('/html-schema/<string:language>/<string:className>')
def htmlSchema(language='NONE', className='NONE'):
    CLASS_ROOT = "http://data.rdlabs.beeldengeluid.nl/schema"
    DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"
    RANGE = "http://www.w3.org/2000/01/rdf-schema#range"
    SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
    bengClasses = []
    bengProps = []

    with open('../resource/bengSchema.json', 'r') as bengSchema:
        data = bengSchema.read()
    obj = json.loads(data)

    # setting default language if none provided.
    if language == 'NONE':
        language = 'nl'

    if className != 'NONE':
        classProps = []
        for d in obj:
            for k, v in d.items():
                if k and k == '@type' and d[k][0].endswith('Property') and DOMAIN in d:
                    if d[DOMAIN][0]['@id'] == CLASS_ROOT + "/" + className:
                        classProps.append(d)
        # Class with no properties on its own (Abstract Class)
        if len(classProps) > 0:
            return render_template('schema.html', language=language, className=className, classProps=classProps)
        else:
            implementedByClass = []
            rangeOfProperty = []
            for node in obj:
                if SUBCLASS in node:
                    for subClassItem in node[SUBCLASS]:
                        if CLASS_ROOT + "/" + className == subClassItem['@id']:
                            implementedByClass.append(node)
                elif RANGE in node:
                    for rangeItem in node[RANGE]:
                        if CLASS_ROOT + "/" + className == rangeItem['@id']:
                            rangeOfProperty.append(node)
            return render_template('schema.html', language=language, className=className,
                                   rangeOfProperty=rangeOfProperty, implementedByClass=implementedByClass)

    for d in obj:
        # parsing Schema (in json format)
        for k, v in d.items():
            if k and k == '@type' and d[k][0].endswith('Class'):
                bengClasses.append(d)
            elif k and k == '@type' and d[k][0].endswith('Property'):
                bengProps.append(d)
    return render_template('schema.html', language=language, bengClasses=bengClasses, bengProps=bengProps)


# @app.route('/docs/')
# def docs():
#     return render_template('docs/index.html')
#
#
# @app.route('/docs/static/<path:path>/')
# def docs_static(path):
#     print(path)
#     # Try to have the HTML from templates use these static files.
#     # Already tried:
#     # return url_for('static', filename=doc_path)
#     # return render_template(doc_path)
#     # return send_from_directory('/home/wmelder/PycharmProjects/beng-lod-server/src/static', doc_path)
#
#     return send_from_directory('static', path)


# @app.route('/docs/<path:path>')
# def docs_templates(path):
#     if os.path.dirname(path).startswith('static'):
#         print(path)
#         # Try to have the HTML from templates use these static files.
#         # Already tried:
#         # return url_for('static', filename=doc_path)
#         # return render_template(doc_path)
#         return send_from_directory('static', path)
#     else:
#         template_path = '/'.join(['docs', path])
#         # print(template_path)
#         return render_template(template_path)


@app.route('/docs/')
def docs():
    return send_from_directory(os.path.join(Path(app.static_folder).parent, 'docs'), 'index.html')
    # return redirect(url_for('docs'))


# @app.route('/docs/entities-az.html/', endpoint='entities-az')
# def docs_entities_az():
#     return send_from_directory('docs', 'entities-az.html')


@app.route('/docs/<path:path>')
def docs_path(path):
    return send_from_directory(os.path.join(Path(app.static_folder).parent, 'docs'), path)

#
# @app.route('/docs/entities-az.html/<path:path>')
# def docs_entities_az_path(path):
#     return send_from_directory('docs', path)
#
#
# @app.route('/docs/statistics.html/<path:path>')
# def docs_statistics_path(path):
#     return send_from_directory('docs', path)
#
#
# @app.route('/docs/entities-tree-classes.html/<path:path>')
# def docs_entities_tree_classes_path(path):
#     return send_from_directory('docs', path)
#
#
# @app.route('/docs/entities-tree-properties.html/<path:path>')
# def docs_entities_tree_properties_path(path):
#     return send_from_directory('docs', path)


# @app.route('/docs/<string:page_name>', endpoint='docs')
# def render_static(page_name):
#     return send_from_directory('docs', page_name)
#     # return render_template('docs/%s' % page_name)
#     # return send_from_directory('/var/www/docs', page_name)


# @app.route('/docs/<string:html_page>/<path:path>')
# def docs_html_page_path(html_page, path):
#     if path is None:
#         return send_from_directory('docs', html_page)
#     if html_page.endswith('html'):
#         return send_from_directory('docs', path)
#     return send_from_directory('docs', os.path.join(html_page, path))


# @app.route('/docs/<string:html_page>/<path:path>')
# def render_static_html_page(html_page, path):
#     if path is None:
#         # Already tried
#         # return send_from_directory('docs', html_page)
#         return render_template('docs/%s' % html_page)
#     if html_page.endswith('html'):
#         # tried earlier
#         # return send_from_directory('docs', path)
#         return render_template('docs/%s' % path)
#     # tried
#     # return send_from_directory('docs', os.path.join(html_page, path))
#     return render_template('docs/%s/%s' % (html_page, path))


# @app.route('/docs/static/libs/bootswatch3_2/yeti/fonts/<path:path>')
# def docs_fonts_path(path):
#     return send_from_directory('docs/static/libs/bootstrap-3_3_7-dist/fonts', path)


# @app.route('/docs/<path:path>')
# def docs_path(path):
#     return send_from_directory('docs', path)


if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
