from datetime import datetime

ERROR_RESPONSES = {
	'access_denied' : {
		'msg' : 'Access denied',
		'code' : 403
	},
	'bad_request' : {
		'msg' : 'Bad request, please provide the correct parameters',
		'code' : 400
	},
	'not_found' : {
		'msg' : 'Resource not found',
		'code' : 404
	},
	'internal_server_error' : {
		'msg' : 'Internal server error',
		'code' : 500
	}
}

class APIUtil:

	@staticmethod
	def matchesErrorId(msg, errorId):
		errorMessage, explanation = APIUtil.parseErrorMessage(msg)
		return errorMessage == APIUtil.toErrorMessage(errorId)

	@staticmethod
	def raiseDescriptiveValueError(errorId, explanation):
		raise ValueError('%s: %s' % (errorId, explanation))

	@staticmethod
	def toErrorMessage(errorId):
		if errorId in ERROR_RESPONSES:
			return ERROR_RESPONSES[errorId]['msg']
		return None

	@staticmethod
	def parseErrorMessage(msg):
		if msg == None:
			return '', None
		tmp = msg.split(': ')
		if len(tmp) == 1:
			tmp.append(None)
		return tmp[0], tmp[1]

	@staticmethod
	def toParsedErrorResponse(msg):
		errorId, explanation = APIUtil.parseErrorMessage(msg)
		return APIUtil.toErrorResponse(errorId, explanation)

	@staticmethod
	def toErrorResponse(errorId, explanation=None):
		msg = 'An unknown error OCURRIO: %s' % errorId
		code = 500
		if errorId in ERROR_RESPONSES:
			msg = ERROR_RESPONSES[errorId]['msg']
			if explanation:
				msg += ': %s' % explanation
			code = ERROR_RESPONSES[errorId]['code']
		return APIUtil.getErrorMessage(msg), code, None

	@staticmethod
	def toSuccessResponse(data, headers={'Access-Control-Allow-Credentials' : 'true'}):
		return data, 200, headers

	@staticmethod
	def getErrorMessage(msg):
		return {'error' : msg}

	@staticmethod
	def getSuccessMessage(msg, data):
		return {'success' : msg, 'data' : data}

	@staticmethod
	def addProvenance(collectionId, response, query, config):
		response['query'] = query
		response['timestamp'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
		response['service'] = {
			"name": "Beeld en Geluid search API",
			"version": config['APP_VERSION'],
			"collection": collectionId,
			"dependencies": [
				"ElasticSearch 5",
				"CKAN"
			]
		}
