import pytest
from mockito import when, unstub
from apis.lod.LODHandlerConcept import LODHandlerConcept
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

DUMMY_SET = "dummy-set"
DUMMY_NOTATION = "dummy-notation"


@pytest.mark.parametrize('concept_uri',  ['http://vanhetneppadjeaf.com', 'file://bestaatnietman', 'geeneens een url', 'fake://hahahaha'])
def test_get_concept_rdf__invalid_concept_uri(application_settings, concept_uri):
    try:
        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).get_concept_uri(DUMMY_SET, DUMMY_NOTATION).thenReturn(concept_uri)
        data, status_code, headers = handler_concept.get_concept_rdf(DUMMY_SET, DUMMY_NOTATION, return_format=format)
        assert 'error' in data
        assert APIUtil.matchesErrorId(data['error'], 'bad_request')
    finally:
        unstub()


def test_get_concept_rdf__invalid_return_format(application_settings, get_concept_rdf_url):
    try:
        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).get_concept_uri(DUMMY_SET, DUMMY_NOTATION).thenReturn(get_concept_rdf_url)
        data, status_code, headers = handler_concept.get_concept_rdf(DUMMY_SET, DUMMY_NOTATION, return_format='DIKKENEPZOOI')
        assert 'error' in data
        assert APIUtil.matchesErrorId(data['error'], 'bad_request')
    finally:
        unstub()


@pytest.mark.parametrize('ld_format',  ['xml', 'json-ld', 'ttl', 'n3'])
def test_get_concept_rdf__succes(application_settings, ld_format, get_concept_rdf_url):
    try:
        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).get_concept_uri(DUMMY_SET, DUMMY_NOTATION).thenReturn(get_concept_rdf_url)
        data, status_code, headers = handler_concept.get_concept_rdf(DUMMY_SET, DUMMY_NOTATION, return_format=ld_format)
        assert status_code == 200

    finally:
        unstub()
