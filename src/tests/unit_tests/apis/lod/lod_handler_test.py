import pytest
from mockito import when, unstub, verify
from apis.lod.LODHandler import LODHandler
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

DUMMY_ID = 'dummy_id'
DUMMY_LEVEL = 'program'
DUMMY_XSLT_FILE = 'dummy_file_that_does_not_exist'
DUMMY_URI_ERROR = 'this_is_really_not_an_existing_uri'


def test_LODHandler_xslt_not_found():
    lodHandler = None
    try:
        lodHandler = LODHandler({'XSLT_FILE': DUMMY_XSLT_FILE})
    except ValueError as e:
        assert APIUtil.valueErrorContainsErrorId(e, 'internal_server_error')
        assert lodHandler is None
    finally:
        unstub()


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


@pytest.mark.parametrize('return_type', ['json-ld', 'xml', 'n3', 'ttl'])
def test_getOAIRecord_200(application_settings, get_record_xml_local_uri, return_type):
    try:
        lodHandler = LODHandler(application_settings)
        when(LODHandler)._prepareURI(DUMMY_LEVEL, DUMMY_ID).thenReturn(get_record_xml_local_uri)
        data, status_code, headers = lodHandler.getOAIRecord(DUMMY_LEVEL, DUMMY_ID, return_type)

        assert status_code == 200

        # make sure the returned data is of the intended format
        if return_type == 'json-ld':
            assert APIUtil.isValidJSON(data) is True
        elif return_type == 'xml':
            assert APIUtil.isValidXML(data) is True

        # make sure the RDF can be parsed
        assert APIUtil.isValidRDF(data=data, return_format=return_type) is True

        verify(LODHandler, times=1)._prepareURI(DUMMY_LEVEL, DUMMY_ID)
    finally:
        unstub()


def test_getOAIRecord_400(application_settings, o_get_record):
    try:
        lodHandler = LODHandler(application_settings)
        when(LODHandler)._prepareURI(DUMMY_LEVEL, DUMMY_ID).thenReturn(DUMMY_URI_ERROR)
        resp, status_code, headers = lodHandler.getOAIRecord(DUMMY_LEVEL, DUMMY_ID, 'FAKE')

        assert status_code == 400
        assert 'error' in resp
        assert APIUtil.matchesErrorId(resp['error'], 'bad_request')

        verify(LODHandler, times=1)._prepareURI(DUMMY_LEVEL, DUMMY_ID)
    finally:
        unstub()
