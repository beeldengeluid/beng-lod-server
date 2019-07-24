from lxml import etree
from lxml.etree import XMLSyntaxError
import json
from rdflib import Graph
from rdflib.exceptions import ParserError


ERROR_RESPONSES = {
	'access_denied': {
		'msg': 'Access denied',
		'code': 403
	},
	'bad_request': {
		'msg': 'Bad request, please provide the correct parameters',
		'code': 400
	},
	'not_found': {
		'msg': 'Resource not found',
		'code': 404
	},
	'internal_server_error': {
		'msg': 'Internal server error',
		'code': 500
	}
}

class APIUtil:

	@staticmethod
	def matchesErrorId(msg, errorId):
		errorMessage, explanation = APIUtil.parseErrorMessage(msg)
		return errorMessage == APIUtil.toErrorMessage(errorId)

	@staticmethod
	def valueErrorContainsErrorId(valueError, errorId):
		if not type(valueError) == ValueError:
			return False
		errorMessage, explanation = APIUtil.parseErrorMessage(str(valueError))
		return errorMessage == errorId

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
		if msg is None:
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
	def toSuccessResponse(data, headers=None):
		if headers is None:
			headers = {'Access-Control-Allow-Credentials': 'true'}
		return data, 200, headers

	@staticmethod
	def getErrorMessage(msg):
		return {'error': msg}

	@staticmethod
	def getSuccessMessage(msg, data):
		return {'success': msg, 'data': data}

	@staticmethod
	def isValidJSON(data):
		try:
			json.loads(data)
		except ValueError as e:
			return False
		return True

	@staticmethod
	def isValidXML(data):
		try:
			etree.fromstring(data)
		except XMLSyntaxError as e:
			return False
		return True

	@staticmethod
	def isValidRDF(data, format=None):
		try:
			graph = Graph()
			graph.parse(data=data, format=format)
		except ParserError as exc:
			print(exc)
			return False
		return True
