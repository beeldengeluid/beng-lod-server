import pytest
import json
from lxml import etree
from mockito import when, unstub, verify
from apis.dataset.DataCatalogLODHandler import DataCatalogLODHandler
from util.ld_util import generate_lod_resource_uri
from models.DAANRdfModel import ResourceURILevel
from apis.mime_type_util import MimeType
from rdflib.plugin import PluginException

# this "dummy data" relies on the ./resources/daan-catalog_unit_test.ttl
# which is loaded in memory (as rdflib graph) on DataCatalogLODHandler init
# all unit tests assume the data, from said file, is loaded in memory
DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"
DUMMY_DATASET_ID = "0001"
DUMMY_DATASET_URI = generate_lod_resource_uri(
    ResourceURILevel.DATASET,
    DUMMY_DATASET_ID,
    DUMMY_BENG_DATA_DOMAIN
)
XML_ENCODING_DECLARATION = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"


@pytest.mark.parametrize(
    "dataset_uri, mime_type, valid_dataset",
    [
        (DUMMY_DATASET_URI, MimeType.JSON_LD, True),
        (DUMMY_DATASET_URI, MimeType.JSON_LD, False),  # does not matter if the dataset is valid
        (DUMMY_DATASET_URI, MimeType.RDF_XML, True),
        (DUMMY_DATASET_URI, MimeType.TURTLE, True),
        (DUMMY_DATASET_URI, MimeType.N_TRIPLES, True),
        (DUMMY_DATASET_URI, MimeType.N3, True),
        (DUMMY_DATASET_URI, MimeType.JSON, True),
        (DUMMY_DATASET_URI, "application/phony_mime_type", True),

    ],
)
def test_get_dataset(application_settings, dataset_uri, mime_type, valid_dataset):
    try:
        dch = DataCatalogLODHandler(application_settings)
        when(dch).is_valid_dataset(DUMMY_DATASET_URI).thenReturn(valid_dataset)
        resp, status_code, headers = dch.get_dataset(
            dataset_uri,
            mime_type.to_ld_format() if not type(mime_type) == str else mime_type
        )
        # TODO: test the data in resp
        assert status_code == 200
        if mime_type == MimeType.JSON_LD:
            json_data = json.loads(resp)
            assert type(resp) == str
            assert type(json_data) == dict
        elif mime_type == MimeType.RDF_XML:
            assert type(resp) == str
            assert XML_ENCODING_DECLARATION in resp
            root = etree.fromstring(resp.replace(XML_ENCODING_DECLARATION, ""))
            assert type(root) == etree._Element
        elif mime_type == MimeType.TURTLE:
            assert type(resp) == str
        elif mime_type == MimeType.N_TRIPLES:
            assert type(resp) == str
        elif mime_type == MimeType.N3:
            assert type(resp) == str
        elif mime_type == MimeType.JSON:
            json_data = json.loads(resp)
            assert type(resp) == str
            assert type(json_data) == dict
        verify(dch, times=1).is_valid_dataset(DUMMY_DATASET_URI)
    except PluginException:
        assert mime_type == "application/phony_mime_type"
    finally:
        unstub()

# TODO: test the lod_view for datasets
