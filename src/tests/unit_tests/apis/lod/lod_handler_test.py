import json
import os
import pytest
from mockito import when, KWARGS, unstub, verify
from apis.lod.LODHandler import LODHandler
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

@pytest.mark.parametrize('return_type', [('json-ld'), ('xml'), ('n3'), ('ttl'), ('FAKE')])
def test_fetchDocument_200(application_settings, return_type):
	try:
		lodHandler = LODHandler(application_settings)
		#when(ElasticSearchHandler).get(**KWARGS).thenReturn(o_get_doc)
		resp, status_code, headers = lodHandler.getOAIRecord(
			'program', '3829526', return_type
		)
		if return_type != 'FAKE':
			assert status_code == 200
		else:
			assert status_code == 400

		#verify(ElasticSearchHandler, times=1).get(**KWARGS)
	finally:
		unstub()

