import pytest
from mockito import when, unstub, verify
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SKOS  # type: ignore
import util.ld_util
import util.lodview_util
from apis.gtaa.gtaa_api import GTAAAPI
from util.mime_type_util import MimeType


def test_init():
    gtaa_api = GTAAAPI()
    assert isinstance(gtaa_api, GTAAAPI)


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200(mime_type, flask_test_client):
    """Given a flask_test_client, a mime_type and stubbed invocations, do a
    GET request. Check the status and whether the expected functions are called.
    Note that dummy graph can not be empty, because an error will be raised.
    """
    config = flask_test_client.application.config
    DUMMY_IDENTIFIER = 1234
    PATH = f"gtaa/{DUMMY_IDENTIFIER}"
    DUMMY_URL = f"""{config.get("BENG_DATA_DOMAIN")}{PATH}"""
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_SERIALISED_GRAPH = (
        "just something pretending to be a serialisation of a graph"
    )
    DUMMY_GRAPH = Graph(bind_namespaces="core")
    DUMMY_GRAPH.add((URIRef(DUMMY_URL), RDF.type, SKOS.Concept))

    try:
        when(util.ld_util).is_skos_resource(
            DUMMY_URL, config.get("SPARQL_ENDPOINT", "")
        ).thenReturn(True)
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            config.get("SPARQL_ENDPOINT"),
            config.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_GRAPH)

        if mime_type is MimeType.HTML:
            when(util.lodview_util).generate_html_page(
                DUMMY_GRAPH,
                DUMMY_URL,
                config.get("SPARQL_ENDPOINT"),
            ).thenReturn(DUMMY_PAGE)
        else:
            when(util.lodview_util).get_serialised_graph(
                DUMMY_GRAPH,
                mime_type,
            ).thenReturn(DUMMY_SERIALISED_GRAPH)

        resp = flask_test_client.get(
            PATH,
            headers={"Accept": mime_type.value},
        )
        assert resp.status_code == 200

        verify(util.ld_util, times=1).is_skos_resource(
            DUMMY_URL, config.get("SPARQL_ENDPOINT", "")
        )
        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            config.get("SPARQL_ENDPOINT"),
            config.get("URI_NISV_ORGANISATION"),
        )
        if mime_type is MimeType.HTML:
            verify(util.lodview_util, times=1).generate_html_page(
                DUMMY_GRAPH,
                DUMMY_URL,
                config.get("SPARQL_ENDPOINT"),
            )
        else:
            verify(util.lodview_util, times=1).get_serialised_graph(
                DUMMY_GRAPH,
                mime_type,
            )

    finally:
        unstub()


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200_with_data(mime_type, flask_test_client, i_gtaa_graph):
    """Given a flask_test_client, a mime_type and stubbed invocations, do a
    GET request. A graph will be loaded from a fixture.
    Check the status, whether the expected functions are called and check that
    the output is in valid format.
    """
    config = flask_test_client.application.config
    DUMMY_IDENTIFIER = 1234
    PATH = f"gtaa/{DUMMY_IDENTIFIER}"
    DUMMY_URL = f'{config.get("BENG_DATA_DOMAIN")}{PATH}'

    try:
        when(util.ld_util).is_skos_resource(
            DUMMY_URL, config.get("SPARQL_ENDPOINT", "")
        ).thenReturn(True)
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            config.get("SPARQL_ENDPOINT"),
            config.get("URI_NISV_ORGANISATION"),
        ).thenReturn(i_gtaa_graph)

        resp = flask_test_client.get(
            PATH,
            headers={"Accept": mime_type.value},
        )
        assert resp.status_code == 200

        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            config.get("SPARQL_ENDPOINT"),
            config.get("URI_NISV_ORGANISATION"),
        )

        if mime_type is MimeType.HTML:
            try:
                html_content = resp.text
                assert "<!doctype html>" in html_content
                assert "<html" in html_content
                assert "</html>" in html_content
                assert "LOD View" in html_content

            except (UnicodeDecodeError, AttributeError):
                pytest.fail("HTML output undecodable.")
        else:
            try:
                g = Graph()
                g.parse(data=resp.text, format=mime_type.to_ld_format())
            except Exception:
                pytest.fail(f"Invalid {mime_type} output.")

    finally:
        unstub()


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_404(mime_type, flask_test_client):
    """Given a flask_test_client, a mime_type and stubbed invocations,
    do a GET request and check the status.
    """
    config = flask_test_client.application.config
    DUMMY_IDENTIFIER = 1234
    PATH = f"gtaa/{DUMMY_IDENTIFIER}"
    DUMMY_URL = f'{config.get("BENG_DATA_DOMAIN")}{PATH}'

    try:
        when(util.ld_util).is_skos_resource(
            DUMMY_URL, config.get("SPARQL_ENDPOINT", "")
        ).thenReturn(False)
        resp = flask_test_client.get(
            PATH,
            headers={"Accept": mime_type.value},
        )
        assert resp.status_code == 404
    finally:
        unstub()


@pytest.mark.parametrize(
    "mime_type",
    [mime_type for mime_type in MimeType if mime_type != MimeType.HTML] + [None],
)
def test_get_500(mime_type, flask_test_client, caplog):
    config = flask_test_client.application.config
    DUMMY_IDENTIFIER = 1234
    PATH = f"gtaa/{DUMMY_IDENTIFIER}"
    DUMMY_URL = f'{config.get("BENG_DATA_DOMAIN")}{PATH}'
    DUMMY_EMPTY_GRAPH = Graph()

    try:
        when(util.ld_util).is_skos_resource(
            DUMMY_URL, config.get("SPARQL_ENDPOINT", "")
        ).thenReturn(True)
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            config.get("SPARQL_ENDPOINT"),
            config.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_EMPTY_GRAPH)

        resp = flask_test_client.get(
            PATH,
            headers={"Accept": mime_type.value if mime_type else None},
        )
        assert resp.status_code == 500

    finally:
        unstub()
