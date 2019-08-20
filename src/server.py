from flask import Flask
from flask import render_template
from flask import request, Response
from flask_cors import CORS
from datetime import datetime
import requests

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

# Formats dates to be used in templates
@app.template_filter()
def datetimeformat(value, format='%d, %b %Y'):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime(format)

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

"""------------------------------------------------------------------------------
HTML ROUTING (HTML VIEW)
------------------------------------------------------------------------------"""
@app.route('/resource-html', methods=['GET'])
@app.route('/resource-html/<string:level>/<int:identifier>')
def resource(level=None, identifier=None):
    requestUrl = f"http://0.0.0.0:5309/resource/{level}/{identifier}"
    req = requests.get(requestUrl, headers={'Accept': 'application/ld+json'})
    jsonObj = req.json()
    keys = ["schema:carrierclass","schema:collection", "dc:identifier", "schema:titleValue",
    "schema:creationdate", "schema:summary", "schema:repository", "schema:genre", "schema:theme",
    "schema:broadcaster", "schema:rights", "schema:source", "schema:type", "schema:location",
    "schema:language", "schema:keyword","schema:distributionchannel", "@type"]
    resourceElems = {}
    resourceElems['creators'] = []
    resourceElems['carriers'] = []
    for i in keys:
        for item in jsonObj['@graph']:
            if i in item:
                if i == "@type" and item[i] == 'schema:Creator':
                    resourceElems['creators'].append(item)
                elif i == "@type" and item[i] == 'schema:Carrier':
                    resourceElems['carriers'].append(item)
                elif i != "@type":
                    resourceElems[i] = item[i]

    return render_template('resource.html', level=level, identifier=identifier, resourceElems=resourceElems, headers=jsonObj['@context'], bodyContent=jsonObj['@graph'])

if __name__ == '__main__':
	app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
