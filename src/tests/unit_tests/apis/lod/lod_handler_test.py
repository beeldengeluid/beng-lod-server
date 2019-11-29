import pytest
from mockito import when, unstub, verify, ANY
from apis.lod.DAANLODHandler import DAANLODHandler
from util.APIUtil import APIUtil
from apis.lod.DAANSchemaImporter import DAANSchemaImporter

""" ------------------------ fetchDocument -----------------------"""

DUMMY_ID = 'dummy_id'
DUMMY_LEVEL = 'program'
DUMMY_SCHEMA_FILE = 'dummy_file_that_does_not_exist'
DUMMY_MAPPING_FILE = 'dummy_file_that_does_not_exist'
DUMMY_URI_ERROR = 'this_is_really_not_an_existing_uri'

def test_LODHandler_bad_config():
	lodHandler = None
	try:
		lodHandler = DAANLODHandler({})
	except ValueError as e:
		assert APIUtil.valueErrorContainsErrorId(e, 'internal_server_error')
		assert lodHandler is None
	finally:
		unstub()

def test_LODHandler_schema_not_found():
	lodHandler = None
	try:
		lodHandler = DAANLODHandler({'SCHEMA_FILE': DUMMY_SCHEMA_FILE})
	except ValueError as e:
		assert APIUtil.valueErrorContainsErrorId(e, 'internal_server_error')
		assert lodHandler is None
	finally:
		unstub()

def test_LODHandler_mapping_not_found():
	lodHandler = None
	try:
		lodHandler = DAANLODHandler({'MAPPING_FILE': DUMMY_SCHEMA_FILE})
	except ValueError as e:
		assert APIUtil.valueErrorContainsErrorId(e, 'internal_server_error')
		assert lodHandler is None
	finally:
		unstub()


def test_LODHandler_corrupt_schema(application_settings):
	lodHandler = None
	try:
		when(DAANSchemaImporter).getClasses().thenReturn(None)
		lodHandler = DAANLODHandler(application_settings)
	except ValueError as e:
		assert APIUtil.valueErrorContainsErrorId(e, 'internal_server_error')
		assert lodHandler is None
	finally:
		unstub()


@pytest.mark.parametrize('return_type', ['json-ld', 'xml', 'n3', 'ttl'])
def test_getOAIRecord_200(application_settings, i_program, return_type):
	try:
		lodHandler = DAANLODHandler(application_settings)
		when(DAANLODHandler)._getXMLFromOAI(ANY).thenReturn(i_program)
		data, status_code, headers = lodHandler.getOAIRecord(DUMMY_LEVEL, DUMMY_ID, return_type)

		assert status_code == 200

		# make sure the returned data is of the intended format
		if return_type == 'json-ld':
			assert APIUtil.isValidJSON(data) is True
		elif return_type == 'xml':
			assert APIUtil.isValidXML(data) is True

		# make sure the RDF can be parsed
		assert APIUtil.isValidRDF(data=data, format=return_type) is True

		verify(DAANLODHandler, times=1)._getXMLFromOAI(ANY)
	finally:
		unstub()


def test_getOAIRecord_400(application_settings, o_get_record):
	try:
		lodHandler = DAANLODHandler(application_settings)
		when(DAANLODHandler)._prepareURI(DUMMY_LEVEL, DUMMY_ID).thenReturn(DUMMY_URI_ERROR)
		resp, status_code, headers = lodHandler.getOAIRecord(DUMMY_LEVEL, DUMMY_ID, 'FAKE')

		assert status_code == 400
		assert 'error' in resp
		assert APIUtil.matchesErrorId(resp['error'], 'bad_request')

		verify(DAANLODHandler, times=1)._prepareURI(DUMMY_LEVEL, DUMMY_ID)
	finally:
		unstub()


def test_getOAIRecord_wrong_logtracktype_400(application_settings, i_other_logtrack_item):
	try:
		lodHandler = DAANLODHandler(application_settings)
		when(DAANLODHandler)._getXMLFromOAI(ANY).thenReturn(i_other_logtrack_item)
		resp, status_code, headers = lodHandler.getOAIRecord(DUMMY_LEVEL, DUMMY_ID, 'json-ld')

		assert status_code == 400
		assert 'error' in resp
		assert APIUtil.matchesErrorId(resp['error'], 'bad_request')

		verify(DAANLODHandler, times=1)._getXMLFromOAI(ANY)

	finally:
		unstub()
