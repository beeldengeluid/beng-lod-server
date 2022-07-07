import pytest
import json
from lxml import etree
from mockito import when, unstub, verify, verifyStubbedInvocationsAreUsed
from apis.dataset.DataCatalogLODHandler import DataCatalogLODHandler
from util.ld_util import generate_lod_resource_uri
from models.DAANRdfModel import ResourceURILevel
from apis.mime_type_util import MimeType
from rdflib import Graph
from rdflib.plugin import PluginException

# this "dummy data" relies on the ./resources/daan-catalog_unit_test.ttl
# which is loaded in memory (as rdflib graph) on DataCatalogLODHandler init
# all unit tests assume the data, from said file, is loaded in memory
DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"
DUMMY_DATASET_ID = "0001"
DUMMY_DATASET_URI = generate_lod_resource_uri(
    ResourceURILevel.DATASET, DUMMY_DATASET_ID, DUMMY_BENG_DATA_DOMAIN
)
XML_ENCODING_DECLARATION = '<?xml version="1.0" encoding="utf-8"?>'


@pytest.fixture
def data_catalog_handler(application_settings) -> DataCatalogLODHandler:
    try:
        yield DataCatalogLODHandler(application_settings)
    finally:
        verifyStubbedInvocationsAreUsed()
        unstub()


# TODO: test the data in resp
@pytest.mark.parametrize(
    "dataset_uri, mime_type, valid_dataset",
    [
        (DUMMY_DATASET_URI, MimeType.JSON_LD.to_ld_format(), True),
        (DUMMY_DATASET_URI, MimeType.JSON_LD.to_ld_format(), False),
        (DUMMY_DATASET_URI, MimeType.RDF_XML.to_ld_format(), True),
        (DUMMY_DATASET_URI, MimeType.TURTLE.to_ld_format(), True),
        (DUMMY_DATASET_URI, MimeType.N_TRIPLES.to_ld_format(), True),
        (DUMMY_DATASET_URI, MimeType.N3.to_ld_format(), True),
        (DUMMY_DATASET_URI, "application/phony_mime_type", True),
    ],
)
def test_get_dataset(data_catalog_handler, dataset_uri, mime_type, valid_dataset):
    try:
        # mock result of validity check
        when(data_catalog_handler).is_valid_dataset(DUMMY_DATASET_URI).thenReturn(
            valid_dataset
        )

        # call get_dataset to test results
        resp, status_code, headers = data_catalog_handler.get_dataset(
            dataset_uri, mime_type
        )

        # test if result is expected
        # TODO: if not valid_dataset should receive/test for 404
        if valid_dataset or not valid_dataset:
            assert status_code == 200
            assert type(resp) == str  # TODO: use type annotations instead

            # general deserialization tests for supported rdf serializations
            if mime_type != "application/phony_mime_type":
                Graph().parse(data=resp, format=mime_type)

            # specialized deserialization tests for selected formats
            if mime_type == MimeType.JSON_LD.to_ld_format():
                json.loads(resp)
            elif mime_type == MimeType.RDF_XML.to_ld_format():
                assert XML_ENCODING_DECLARATION in resp
                etree.fromstring(resp.replace(XML_ENCODING_DECLARATION, ""))

            # get_dataset is expected to invoke is_valid_dataset
            verify(data_catalog_handler, times=1).is_valid_dataset(DUMMY_DATASET_URI)
    except PluginException:
        assert mime_type == "application/phony_mime_type"
