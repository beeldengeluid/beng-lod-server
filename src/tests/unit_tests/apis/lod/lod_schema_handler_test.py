import json
import pytest
from mockito import when, KWARGS, unstub, verify, ARGS
from apis.lod.LODSchemaHandler import LODSchemaHandler
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

INVALID_SCHEMA_PATH = './dummy/dummy.ttl'
INVALID_SCHEMA_EXT = './dummy/dummy.xxx'

def test_getSchema_200(application_settings, o_get_schema):
	try:
		schemaHandler = LODSchemaHandler(application_settings)
		resp, status_code, headers = schemaHandler.getSchema()
		assert status_code == 200

	finally:
		unstub()

@pytest.mark.parametrize('invalid_appplication_settings', [
	{'SCHEMA_FILE' : INVALID_SCHEMA_PATH, 'SCHEMA_FILE' : INVALID_SCHEMA_EXT}
])
def test_getSchema_500(o_get_schema, invalid_appplication_settings):
	try:
		schemaHandler = LODSchemaHandler(invalid_appplication_settings)
		resp, status_code, headers = schemaHandler.getSchema()
		assert status_code == 500

	finally:
		unstub()