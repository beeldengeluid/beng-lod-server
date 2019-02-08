from flask import Flask
from flask import render_template
from flask import request, Response
from flask_cors import CORS

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

if __name__ == '__main__':
	app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
