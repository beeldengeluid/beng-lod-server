import pytest
from mockito import when, unstub
from apis.lod.LODHandlerConcept import LODHandlerConcept
from util.APIUtil import APIUtil
from rdflib.plugin import PluginException

""" ------------------------ fetchDocument -----------------------"""

DUMMY_SET = "blabla"
DUMMY_NOTATION = "123456"
RETURN_TYPE = "JSON"
# DUMMY_URI = "http://dummy.test/blabla/123456.rdf"
DUMMY_URI = "file://output_get_concept_rdf.xml"
# DUMMY_DATA = "absolute totally unusable rubbish data without any structure whatsoever"

@pytest.mark.xfail
@pytest.mark.parametrize('format',  ['xml', 'json-ld', 'ttl', 'n3'])
def test_get_concept_rdf_error(application_settings, format, get_concept_rdf_url):
    handler_concept = None
    try:
        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).getConceptUri(DUMMY_SET, DUMMY_NOTATION).thenReturn(get_concept_rdf_url)
        data, status_code, headers = handler_concept.getConceptRDF(DUMMY_SET, DUMMY_NOTATION, return_format=format)
        assert status_code == 400

    except ValueError as e:
        assert APIUtil.valueErrorContainsErrorId(e, 'bad_request')
        assert handler_concept is None
    finally:
        unstub()


@pytest.mark.parametrize('format',  ['xml', 'json-ld', 'ttl', 'n3'])
def test_get_concept_rdf_succes(application_settings, format, get_concept_rdf_url):
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
