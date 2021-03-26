import pytest
from mockito import when, unstub, verify
from apis.lod.OpenDataLabHandler import OpenDataLabHandler
from util.APIUtil import APIUtil

""" ------------------------ fetchDocument -----------------------"""

DUMMY_ID = 'dummy_id'
DUMMY_LEVEL = 'program'
DUMMY_URI_ERROR = 'this_is_really_not_an_existing_uri'

DUMMY_FORMAT = 'json-ld'
DUMMY_INDEX = 'kwaak'
DUMMY_DOC_TYPE = 'blub'
DUMMY_URI = 'http://blab.la/kwaak'


def test_get_dummy_id(application_settings):
    try:
        odl_handler = OpenDataLabHandler(application_settings)
        # TODO: fix the initialisation to the ES server in mock

        doc_id = odl_handler.get_doc_id_from_uri(uri=DUMMY_URI)
        assert doc_id is not None

    finally:
        unstub()


def test_get_aggregated_program_200(application_settings, get_json_doc_program_aggr):
    try:
        odl_handler = OpenDataLabHandler(application_settings)
        when(OpenDataLabHandler).get(document_type=DUMMY_DOC_TYPE, doc_id=DUMMY_ID).thenReturn(
            get_json_doc_program_aggr)
        doc = odl_handler.get(document_type=DUMMY_DOC_TYPE, doc_id=DUMMY_ID)
        assert APIUtil.is_valid_json_dict(doc)

    finally:
        unstub()


@pytest.mark.parametrize('return_format', ['json-ld', 'xml', 'ttl'])
def test_create_rdf(application_settings, get_json_doc_program_aggr, return_format):
    try:
        odl_handler = OpenDataLabHandler(application_settings)
        rdf_data = odl_handler._create_rdf_from_json_dict(json_dict=get_json_doc_program_aggr,
                                                          requested_format=return_format)
        assert APIUtil.isValidRDF(data=rdf_data, return_format=return_format) is True

    finally:
        unstub()


@pytest.mark.parametrize('return_type', ['json-ld', 'xml', 'ttl'])
def test_get_media_item_nisv_200(application_settings, get_json_doc_program_aggr, return_type):
    try:
        odl_handler = OpenDataLabHandler(application_settings)
        when(OpenDataLabHandler).get_doc_id_from_uri(uri=DUMMY_URI).thenReturn(DUMMY_ID)
        when(OpenDataLabHandler).get(document_type=DUMMY_DOC_TYPE, doc_id=DUMMY_ID).thenReturn(
            get_json_doc_program_aggr)
        data, status_code, headers = odl_handler.get_media_item_nisv(DUMMY_DOC_TYPE, DUMMY_URI, ld_format=return_type)

        assert status_code == 200

        # make sure valid RDF is returned
        assert APIUtil.isValidRDF(data=data, return_format=return_type) is True

        verify(OpenDataLabHandler, times=1).get_doc_id_from_uri(uri=DUMMY_URI)
        verify(OpenDataLabHandler, times=1).get(document_type=DUMMY_DOC_TYPE, doc_id=DUMMY_ID)
        # verify(OpenDataLabHandler, times=1)._create_rdf_from_json_dict(json_dict=data)

    finally:
        unstub()


# def test_search_200(application_settings, application_client, i_search, o_search):
#     try:
#         bsHandler = BasicSearchHandler(application_settings)
#         #mock the call to Elasticsearch
#         when(ElasticSearchHandler).search(i_search, 'dummy-collection', None).thenReturn(o_search)
#         resp, status_code, headers = bsHandler.search(
#             application_client['id'],
#             application_client['token'],
#             i_search,
#             DUMMY_COLLECTION #TODO dynamically load this?
#         )
#         assert status_code == 200
#         assert 'error' not in resp
#         assert all(x in ['hits', 'service', 'timestamp', 'query'] for x in resp)
#         assert all(type(resp[x]) == dict for x in ['hits', 'service', 'query'])
#         assert type(datetime.strptime(resp['timestamp'], '%Y-%m-%dT%H:%M:%SZ')) == datetime
#         assert 'hits' in resp['hits']
#         assert type(resp['hits']['hits']) == list
#         verify(ElasticSearchHandler, times=1).search(i_search, DUMMY_COLLECTION, None)
#     finally:
#         unstub()