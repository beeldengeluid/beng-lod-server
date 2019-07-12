# TODO: create a fixture for a skos concept
# TODO: create parametrize argument for test_get_concept_rdf
# TODO: test these possible return values:
# return APIUtil.toSuccessResponse(data)
# return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')

import pytest
from mockito import when, unstub, verify
from apis.lod.LODHandlerConcept import LODHandlerConcept
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

DUMMY_ID = 'dummy_id'
DUMMY_LEVEL = 'program'
DUMMY_XSLT_FILE = 'dummy_file_that_does_not_exist'


def test_get_concept_rdf(application_settings):
    handler_concept = None
    try:
        handler_concept = LODHandlerConcept(application_settings)
    except ValueError as e:
        assert APIUtil.valueErrorContainsErrorId(e, 'bad_request')
        assert handler_concept is None
    finally:
        unstub()
