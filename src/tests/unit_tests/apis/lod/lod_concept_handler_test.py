import pytest
from mockito import when, unstub
from apis.lod.LODHandlerConcept import LODHandlerConcept
from util.APIUtil import APIUtil
from rdflib.plugin import PluginException

""" ------------------------ fetchDocument -----------------------"""

DUMMY_SET = "dummy-set"
DUMMY_NOTATION = "dummy-notation"

# @pytest.mark.xfail
@pytest.mark.parametrize('concept_uri',  ['http://vanhetneppadjeaf.com', 'file://bestaatnietman', 'geeneens een url', 'fake://hahahaha'])
def test_get_concept_rdf__invalid_concept_uri(application_settings, concept_uri):
    try:

        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).getConceptUri(DUMMY_SET, DUMMY_NOTATION).thenReturn(concept_uri)
        data, status_code, headers = handler_concept.getConceptRDF(DUMMY_SET, DUMMY_NOTATION, return_format=format)
        assert 'error' in data
        assert APIUtil.matchesErrorId(data['error'], 'bad_request')
    finally:
        unstub()

def test_get_concept_rdf__invalid_return_format(application_settings, get_concept_rdf_url):
    try:

        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).getConceptUri(DUMMY_SET, DUMMY_NOTATION).thenReturn(get_concept_rdf_url)
        data, status_code, headers = handler_concept.getConceptRDF(DUMMY_SET, DUMMY_NOTATION, return_format='DIKKENEPZOOI')
        assert 'error' in data
        assert APIUtil.matchesErrorId(data['error'], 'bad_request')
    finally:
        unstub()

@pytest.mark.parametrize('format',  ['xml', 'json-ld', 'ttl', 'n3'])
def test_get_concept_rdf__succes(application_settings, format, get_concept_rdf_url):
    try:
        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).getConceptUri(DUMMY_SET, DUMMY_NOTATION).thenReturn(get_concept_rdf_url)
        data, status_code, headers = handler_concept.getConceptRDF(DUMMY_SET, DUMMY_NOTATION, return_format=format)
        assert status_code == 200

        # make sure the returned data is of the intended format
        if format == 'json-ld':
            assert APIUtil.isValidJSON(data) is True
        elif format == 'xml':
            assert APIUtil.isValidXML(data) is True

        # make sure the RDF can be parsed
        assert APIUtil.isValidRDF(data=data, format=format) is True

    except PluginException as e:
        print(e)
    except Exception as e:
        print(e)

    finally:
        unstub()
