import pytest
from mockito import unstub
from apis.lod.LODSchemaHandler import LODSchemaHandler
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

INVALID_SCHEMA_PATH = './dummy/dummy.ttl'


def test_getSchema_200(application_settings, o_get_schema):
	try:
		schemaHandler = LODSchemaHandler(application_settings)
		resp, status_code, headers = schemaHandler.getSchema()
		#assert status_code == 200

	finally:
		unstub()


@pytest.mark.parametrize('invalid_appplication_settings', [
	{'SCHEMA_FILE': INVALID_SCHEMA_PATH}
])
def test_getSchema_500(o_get_schema, invalid_appplication_settings):
	try:
		schemaHandler = LODSchemaHandler(invalid_appplication_settings)
		resp, status_code, headers = schemaHandler.getSchema()
		assert status_code == 500
		assert 'error' in resp
		assert APIUtil.matchesErrorId(resp['error'], 'internal_server_error')

	finally:
		unstub()
