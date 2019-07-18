# TODO: create a fixture for a skos concept

import pytest
from mockito import when, unstub, verify
from apis.lod.LODHandlerConcept import LODHandlerConcept
from util.APIUtil import APIUtil
from rdflib import Graph

""" ------------------------ fetchDocument -----------------------"""

DUMMY_SET = "blabla"
DUMMY_NOTATION = "123456"
RETURN_TYPE = "JSON"
DUMMY_URI = "http://dummy.data/blabla/123456.rdf"

@pytest.mark.parametrize('returnFormat',  [ 'xml', 'json-ld', 'ttl', 'n3'] )
def test_get_concept_rdf_error(application_settings, returnFormat, o_get_concept_rdf):
    handler_concept = None
    try:
        handler_concept = LODHandlerConcept(application_settings)
        when(LODHandlerConcept).getConceptUri(DUMMY_SET, DUMMY_NOTATION).thenReturn(o_get_concept_rdf)
        resp, status_code, headers = handler_concept.getConceptRDF(DUMMY_SET, DUMMY_NOTATION, returnFormat=returnFormat)
        assert status_code == 200

        # make sure the returned data is of the intended format
        if RETURN_TYPE == 'json-ld':
            assert APIUtil.isValidJSON(resp)
        elif RETURN_TYPE == 'xml':
            assert APIUtil.isValidXML(resp)
        elif RETURN_TYPE in ['n3', 'ttl']:
            assert APIUtil.isValidRDF(resp)

    except ValueError as e:
        assert APIUtil.valueErrorContainsErrorId(e, 'bad_request')
        assert handler_concept is None
    finally:
        unstub()


# @pytest.mark.parametrize('returnFormat',  [ 'xml', 'json-ld', 'ttl', 'n3'] )
# def test_get_concept_rdf_succes(application_settings, returnFormat):
#     # TODO:
#     # return APIUtil.toSuccessResponse(data)
#     pass
