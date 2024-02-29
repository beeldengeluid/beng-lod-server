import pytest

from mockito import when

import apis.dataset.DataCatalogLODHandler


from util.ld_util import generate_lod_resource_uri
from models.ResourceURILevel import ResourceURILevel
from util.mime_type_util import MimeType
from rdflib import Graph
from rdflib.compare import to_isomorphic, graph_diff
from rdflib.plugin import PluginException

# this "dummy data" relies on the ./resources/daan-catalog_unit_test.ttl
# which is loaded in memory (as rdflib graph) on DataCatalogLODHandler init
# all unit tests mock the relevant function of the DataCatlogLODHandler to
# load these instead of live data

DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"

DUMMY_DATA_DOWNLOAD_ID = "0001"
DUMMY_DATA_DOWNLOAD_URI = generate_lod_resource_uri(
    ResourceURILevel.DATADOWNLOAD, DUMMY_DATA_DOWNLOAD_ID, DUMMY_BENG_DATA_DOMAIN
)


DUMMY_DATASET_ID = "0001"
DUMMY_DATASET_URI = generate_lod_resource_uri(
    ResourceURILevel.DATASET, DUMMY_DATASET_ID, DUMMY_BENG_DATA_DOMAIN
)

DUMMY_DATA_CATALOG_ID = "0001"
DUMMY_DATA_CATALOG_URI = generate_lod_resource_uri(
    ResourceURILevel.DATACATALOG, DUMMY_DATA_CATALOG_ID, DUMMY_BENG_DATA_DOMAIN
)

XML_ENCODING_DECLARATION = '<?xml version="1.0" encoding="utf-8"?>'


def test_init(application_settings):
    data_catalog_lod_handler = apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler(
        application_settings
    )
    assert isinstance(
        data_catalog_lod_handler,
        apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler,
    )


@pytest.mark.parametrize(
    "data_catalog_uri, mime_type",
    [
        (DUMMY_DATA_CATALOG_URI, MimeType.JSON_LD.to_ld_format()),
        (DUMMY_DATA_CATALOG_URI, MimeType.RDF_XML.to_ld_format()),
        (DUMMY_DATA_CATALOG_URI, MimeType.TURTLE.to_ld_format()),
        (DUMMY_DATA_CATALOG_URI, MimeType.N_TRIPLES.to_ld_format()),
        (DUMMY_DATA_CATALOG_URI, MimeType.N3.to_ld_format()),
        (DUMMY_DATA_CATALOG_URI, "application/phony_mime_type"),
    ],
)
def test_get_data_catalog(
    application_settings, data_catalog_uri, i_datacatalog, mime_type
):
    try:
        with (
            when(apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler)
            ._get_data_catalog_from_store(
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("DATA_CATALOG_GRAPH"),
            )
            .thenReturn(i_datacatalog)
        ):
            data_catalog_lod_handler = (
                apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler(
                    application_settings
                )
            )

            # call get_data_catalog to test results
            resp = data_catalog_lod_handler.get_data_catalog(
                data_catalog_uri, mime_type
            )

            assert isinstance(resp, str)  # TODO: use type annotations instead

            # test if serialization is as expected
            if mime_type != "application/phony_mime_type":
                output_graph = Graph().parse(data=resp, format=mime_type)

                # check if it matches the mock input
                iso_input = to_isomorphic(i_datacatalog)
                iso_output = to_isomorphic(output_graph)
                in_both, in_first, in_second = graph_diff(iso_input, iso_output)

                # the input graph may contain several items that are not part of
                # the output graph. But never the other way around.
                # We may have to improve the importer to make sure that all
                # imported items are valid.

                assert len(in_second) == 0
                # assert iso_input == iso_output

    except PluginException:
        assert mime_type == "application/phony_mime_type"


@pytest.mark.parametrize(
    "data_download_uri, mime_type",
    [
        (DUMMY_DATA_DOWNLOAD_URI, MimeType.JSON_LD.to_ld_format()),
        (DUMMY_DATA_DOWNLOAD_URI, MimeType.RDF_XML.to_ld_format()),
        (DUMMY_DATA_DOWNLOAD_URI, MimeType.TURTLE.to_ld_format()),
        (DUMMY_DATA_DOWNLOAD_URI, MimeType.N_TRIPLES.to_ld_format()),
        (DUMMY_DATA_DOWNLOAD_URI, MimeType.N3.to_ld_format()),
        (DUMMY_DATA_DOWNLOAD_URI, "application/phony_mime_type"),
    ],
)
def test_get_data_download(
    application_settings, data_download_uri, i_datacatalog, i_datadownload, mime_type
):
    try:
        with (
            when(apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler)
            ._get_data_catalog_from_store(
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("DATA_CATALOG_GRAPH"),
            )
            .thenReturn(i_datacatalog)
        ):
            data_catalog_lod_handler = (
                apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler(
                    application_settings
                )
            )
            # call get_data_download to test results
            resp = data_catalog_lod_handler.get_data_download(
                data_download_uri, mime_type
            )

            assert isinstance(resp, str)  # TODO: use type annotations instead

            # test if serialization is as expected
            if mime_type != "application/phony_mime_type":
                output_graph = Graph().parse(data=resp, format=mime_type)

                # check if it matches the mock input
                iso_input = to_isomorphic(i_datadownload)
                iso_output = to_isomorphic(output_graph)
                # in_both, in_first, in_second = graph_diff(iso_input, iso_output)
                assert iso_input == iso_output

    except PluginException:
        assert mime_type == "application/phony_mime_type"


@pytest.mark.parametrize(
    "dataset_uri, mime_type",
    [
        (DUMMY_DATASET_URI, MimeType.JSON_LD.to_ld_format()),
        (DUMMY_DATASET_URI, MimeType.RDF_XML.to_ld_format()),
        (DUMMY_DATASET_URI, MimeType.TURTLE.to_ld_format()),
        (DUMMY_DATASET_URI, MimeType.N_TRIPLES.to_ld_format()),
        (DUMMY_DATASET_URI, MimeType.N3.to_ld_format()),
        (DUMMY_DATASET_URI, "application/phony_mime_type"),
    ],
)
def test_get_dataset(
    application_settings, i_datacatalog, i_dataset, dataset_uri, mime_type
):
    try:
        with (
            when(apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler)
            ._get_data_catalog_from_store(
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("DATA_CATALOG_GRAPH"),
            )
            .thenReturn(i_datacatalog)
        ):
            data_catalog_lod_handler = (
                apis.dataset.DataCatalogLODHandler.DataCatalogLODHandler(
                    application_settings
                )
            )

        # call get_dataset to test results
        resp = data_catalog_lod_handler.get_dataset(dataset_uri, mime_type)

        # test if result is expected
        assert isinstance(resp, str)  # TODO: use type annotations instead

        # general deserialization tests for supported rdf serializations
        if mime_type != "application/phony_mime_type":
            output_graph = Graph().parse(data=resp, format=mime_type)

            # check if it matches the mock input
            iso_input = to_isomorphic(i_dataset)
            iso_output = to_isomorphic(output_graph)
            assert iso_input == iso_output

    except PluginException:
        assert mime_type == "application/phony_mime_type"
