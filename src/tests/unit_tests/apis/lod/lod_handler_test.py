import json
import pytest
from mockito import when, KWARGS, unstub, verify, ARGS
from apis.lod.LODHandler import LODHandler
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

DUMMY_ID = 'dummy_id'
DUMMY_LEVEL = 'program'

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