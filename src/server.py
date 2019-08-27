from flask import Flask
from flask import render_template
from flask import request, Response
from flask_cors import CORS
import json

from apis import api

app = Flask(__name__)

#init the config
app.config.from_object('settings.Config')
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['RESTPLUS_VALIDATE'] = False

app.debug = app.config['DEBUG']

CORS(app)

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
    return value[lastIndex+1:len(value)]

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
@app.route('/html-schema/<string:language>/', defaults={'className': 'NONE'})
@app.route('/html-schema/<string:language>/<string:className>')
def htmlSchema(language=None, className=None):
    CLASS_ROOT = "http://data.rdlabs.beeldengeluid.nl/schema"
    DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"
    RANGE = "http://www.w3.org/2000/01/rdf-schema#range"
    bengClasses = []
    bengProps = []

    with open('../resource/bengSchema.json', 'r') as bengSchema:
        data = bengSchema.read()
    obj = json.loads(data)

    # parse class properties to feed table
    if className != 'NONE':
        classProps = []
        for d in obj:
            for k, v in d.items():
                if k and k == '@type' and d[k][0].endswith('Property') and DOMAIN in d:
                   dom = d[DOMAIN][0]['@id'] == CLASS_ROOT + "/" + className
                   if d[DOMAIN][0]['@id'] == CLASS_ROOT + "/" + className:
                       classProps.append(d)
        print(len(classProps))
        if len(classProps) == 0:
            print("no own props!")
        return render_template('schema.html', language=language, className=className, classProps=classProps)
    for d in obj:
        # parsing Schema (in json format)
        for k, v in d.items():
            if k and k == '@type' and d[k][0].endswith('Class'):
                bengClasses.append(d)
            elif k and k == '@type' and d[k][0].endswith('Property'):
                bengProps.append(d)
    return render_template('schema.html', language=language, bengClasses=bengClasses, bengProps=bengProps)

if __name__ == '__main__':
	app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
