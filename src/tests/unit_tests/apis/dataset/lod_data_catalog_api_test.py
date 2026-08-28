import pytest
from flask import Response
from mockito import ANY, when, verify, unstub
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SDO  # type: ignore
from rdflib.compare import to_isomorphic
import util.ld_util
import apis.dataset.dataset_api
from models.DatasetApiUriLevel import DatasetApiUriLevel
from util.mime_type_util import MimeType
import util.lodview_util

DUMMY_IDENTIFIER = "1234"
DUMMY_URI = f"http://{DUMMY_IDENTIFIER}"
DUMMY_PAGE = (
    "<!DOCTYPE html> <html> just something pretending to be an interesting "
    "HTML page</html>"
)


def dummy_data_catalog_graph() -> Graph:
    """Returns a minimal graph describing a data catalog."""
    rdf_graph = Graph()
    rdf_graph.add((URIRef(DUMMY_URI), RDF.type, SDO.DataCatalog))
    rdf_graph.add((URIRef(DUMMY_URI), SDO.name, Literal("Dummy data catalog")))
    return rdf_graph


def stub_data_catalog(application_settings):
    """Stub the data catalog that the DataCatalogLODHandler loads on construction,
    so no SPARQL endpoint is queried."""
    when(apis.dataset.dataset_api.DataCatalogLODHandler)._get_data_catalog_from_store(
        application_settings.get("SPARQL_ENDPOINT"),
        application_settings.get("DATA_CATALOG_GRAPH"),
    ).thenReturn(Graph())


def test_init():
    lod_data_catalog_api = apis.dataset.dataset_api.LODDataCatalogAPI()
    assert isinstance(lod_data_catalog_api, apis.dataset.dataset_api.LODDataCatalogAPI)


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200(mime_type, application_settings, flask_test_client, datacatalog_url):
    """Given a valid data catalog, a get request should return the data catalog in the
    requested serialisation, or an HTML page when HTML is requested."""
    data_catalog_graph = dummy_data_catalog_graph()

    try:
        stub_data_catalog(application_settings)
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.DataCatalogLODHandler).get_data_catalog(
            DUMMY_URI, MimeType.TURTLE.value
        ).thenReturn(
            data_catalog_graph.serialize(format=MimeType.TURTLE.to_ld_format())
        )
        when(util.lodview_util).generate_html_page(
            ANY,
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT", ""),
        ).thenReturn(Response(DUMMY_PAGE, mimetype=MimeType.HTML.value))

        resp = flask_test_client.get(
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 200

        if mime_type is MimeType.HTML:
            assert resp.text == DUMMY_PAGE
        else:
            served_graph = Graph()
            try:
                served_graph.parse(data=resp.text, format=mime_type.to_ld_format())
            except Exception:
                pytest.fail(f"Invalid {mime_type} output")
            assert to_isomorphic(served_graph) == to_isomorphic(data_catalog_graph)

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=1
        ).is_valid_data_catalog(DUMMY_URI)
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler, times=1
        ).get_data_catalog(DUMMY_URI, MimeType.TURTLE.value)
        verify(
            util.lodview_util, times=1 if mime_type is MimeType.HTML else 0
        ).generate_html_page(
            ANY,
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT", ""),
        )

    finally:
        unstub()


def test_get_200_mime_type_none(
    application_settings, flask_test_client, datacatalog_url
):
    """Tests the default behaviour for the mime type, which is currently to set it
    to JSON-LD if the input is None"""
    data_catalog_graph = dummy_data_catalog_graph()
    input_mime_type = None
    default_mime_type = MimeType.JSON_LD

    try:
        stub_data_catalog(application_settings)
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.DataCatalogLODHandler).get_data_catalog(
            DUMMY_URI, MimeType.TURTLE.value
        ).thenReturn(
            data_catalog_graph.serialize(format=MimeType.TURTLE.to_ld_format())
        )

        resp = flask_test_client.get(
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": input_mime_type},
        )

        assert resp.status_code == 200
        assert resp.mimetype == default_mime_type.value

        served_graph = Graph()
        served_graph.parse(data=resp.text, format=default_mime_type.to_ld_format())
        assert to_isomorphic(served_graph) == to_isomorphic(data_catalog_graph)

        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler, times=1
        ).get_data_catalog(DUMMY_URI, MimeType.TURTLE.value)

    finally:
        unstub()


@pytest.mark.parametrize("identifier", ["not-a-number", "12a4"])
def test_get_400_invalid_identifier(flask_test_client, datacatalog_url, identifier):
    """A data catalog identifier that is not a number results in a bad request
    response."""
    resp = flask_test_client.get(datacatalog_url(identifier))

    assert resp.status_code == 400
    assert f"Invalid identifier supplied: {identifier}" in resp.text


@pytest.mark.parametrize("mime_type", [MimeType.HTML, MimeType.JSON_LD])
def test_get_400_invalid_data_catalog(
    mime_type, application_settings, flask_test_client, datacatalog_url, caplog
):
    """An existing, but invalid data catalog results in a bad request response."""
    try:
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(False)

        resp = flask_test_client.get(
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 400
        assert f"The data catalog is invalid: {DUMMY_URI}." in caplog.text

        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=1
        ).is_valid_data_catalog(DUMMY_URI)

    finally:
        unstub()


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_404(
    mime_type, application_settings, flask_test_client, datacatalog_url, caplog
):
    """A data catalog that doesn't exist results in a not found response."""
    try:
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(False)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)

        resp = flask_test_client.get(
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 404
        assert f"The data catalog doesn't exist: {DUMMY_URI}." in caplog.text

        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=0
        ).is_valid_data_catalog(DUMMY_URI)

    finally:
        unstub()


@pytest.mark.parametrize("mime_type", [MimeType.HTML, MimeType.JSON_LD])
def test_get_500(
    mime_type, application_settings, flask_test_client, datacatalog_url, caplog
):
    """When no triples are returned for the data catalog, no graph can be created and
    an internal server error response is returned."""
    try:
        stub_data_catalog(application_settings)
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.DataCatalogLODHandler).get_data_catalog(
            DUMMY_URI, MimeType.TURTLE.value
        ).thenReturn(
            Graph().serialize(format=MimeType.TURTLE.to_ld_format())
        )  # empty graph will cause 500

        resp = flask_test_client.get(
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 500
        assert "No graph created" in resp.text

        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler, times=1
        ).get_data_catalog(DUMMY_URI, MimeType.TURTLE.value)

    finally:
        unstub()
