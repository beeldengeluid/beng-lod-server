import json
import pytest
from mockito import when, KWARGS, unstub, verify, ARGS
from apis.lod.LODHandler import LODHandler
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

DUMMY_ID = 'dummy_id'
DUMMY_LEVEL = 'program'
DUMMY_XSLT_FILE = 'dummy_file_that_does_not_exist'

# REMARK: What's the use of a test like this? The code itself checks for existing
# XSLT file. Otherwise it will not continue creation of the LodHandler class.
def test_LODHandler_xslt_not_found():
	lodHandler = None
	try:
		lodHandler = LODHandler({'XSLT_FILE' : DUMMY_XSLT_FILE})
	except ValueError as e:
		assert APIUtil.valueErrorContainsErrorId(e, 'internal_server_error')
		assert lodHandler is None
	finally:
		unstub()

# REMARK: what's the use of this test? The code tests for a valid parseable XSLT itself
# during initialization. If it is not correct it will throw the error as well.
def test_LODHandler_corrupt_xslt(application_settings):
	lodHandler = None
	try:
		lodHandler = LODHandler(application_settings)
		when(LODHandler)._getXSLTTransformer(DUMMY_XSLT_FILE).thenReturn(None)
	except ValueError as e:
		assert APIUtil.valueErrorContainsErrorId(e, 'internal_server_error')
		assert lodHandler is None
	finally:
		unstub()

@pytest.mark.parametrize('return_type', [('json-ld'), ('xml'), ('n3'), ('ttl')])
def test_getOAIRecord_200(application_settings, o_get_record, return_type):
	try:
		lodHandler = LODHandler(application_settings)
		when(LODHandler)._prepareURI(DUMMY_LEVEL, DUMMY_ID).thenReturn(o_get_record)
		resp, status_code, headers = lodHandler.getOAIRecord(DUMMY_LEVEL, DUMMY_ID, return_type)

		assert status_code == 200

		#make sure the returned data is of the intended format
		if return_type == 'json-ld':
			assert APIUtil.isValidJSON(resp)
		elif return_type == 'xml':
			assert APIUtil.isValidXML(resp)
		elif return_type in ['n3', 'ttl']:
			assert not APIUtil.isValidXML(resp)
			assert not APIUtil.isValidJSON(resp)

		verify(LODHandler, times=1)._prepareURI(DUMMY_LEVEL, DUMMY_ID)
	finally:
		unstub()

def test_getOAIRecord_400(application_settings, o_get_record):
	try:
		lodHandler = LODHandler(application_settings)
		when(LODHandler)._prepareURI(DUMMY_LEVEL, DUMMY_ID).thenReturn(o_get_record)
		resp, status_code, headers = lodHandler.getOAIRecord(DUMMY_LEVEL, DUMMY_ID, 'FAKE')

		assert status_code == 400
		assert 'error' in resp
		assert APIUtil.matchesErrorId(resp['error'], 'bad_request')

		verify(LODHandler, times=1)._prepareURI(DUMMY_LEVEL, DUMMY_ID)
	finally:
		unstub()