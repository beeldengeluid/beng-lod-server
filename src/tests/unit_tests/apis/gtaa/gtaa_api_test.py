import json
import pytest

from mockito import when, unstub, verify
from rdflib import Graph

import util.ld_util

from apis.gtaa.gtaa_api import GTAAAPI
from models.ResourceApiUriLevel import ResourceApiUriLevel
from util.mime_type_util import MimeType


def test_init():
    gtaa_api = GTAAAPI()
    assert isinstance(gtaa_api, GTAAAPI)


@pytest.mark.skip(reason="the dummy value is now raising a 404")
# Just tests the flow
@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200(mime_type, generic_client, application_settings, gtaa_url):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f'{application_settings.get("BENG_DATA_DOMAIN")}gtaa/{DUMMY_IDENTIFIER}'
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_SERIALISED_GRAPH = (
        "just something pretending to be a serialisation of a graph"
    )
    CAT_TYPE = "program"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URL)
        if mime_type is MimeType.HTML:
            when(GTAAAPI)._get_lod_view_gtaa(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(DUMMY_PAGE)
        else:
            when(GTAAAPI)._get_lod_gtaa(
                DUMMY_URL,
                mime_type,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(DUMMY_SERIALISED_GRAPH)

        resp = generic_client.get(
            "offline",
            gtaa_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        if mime_type is MimeType.HTML:
            verify(GTAAAPI, times=1)._get_lod_view_gtaa(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            assert resp.text.decode() == DUMMY_PAGE
        else:
            verify(GTAAAPI)._get_lod_gtaa(
                DUMMY_URL,
                mime_type,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            assert resp.text.decode() == DUMMY_SERIALISED_GRAPH

    finally:
        unstub()


@pytest.mark.skip(reason="the new 404 check prevents the verify from being run")
# inserts a real data graph to check the conversions to the right format
@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200_with_data(
    mime_type, generic_client, application_settings, gtaa_url, i_gtaa_graph
):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f'{application_settings.get("BENG_DATA_DOMAIN")}gtaa/{DUMMY_IDENTIFIER}'
    CAT_TYPE = "program"

    try:
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(i_gtaa_graph)

        resp = generic_client.get(
            "offline",
            gtaa_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

        if mime_type is MimeType.HTML:
            try:
                resp.text.decode()
            except (UnicodeDecodeError, AttributeError):
                pytest.fail("HTML output undecodable")
        else:
            try:
                g = Graph()
                g.parse(data=resp.text, format=mime_type.to_ld_format())
            except Exception:
                pytest.fail(f"Invalid {mime_type} output")

    finally:
        unstub()


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
@pytest.mark.skip(reason="the 404 check is better than raising the 500")
@pytest.mark.parametrize(
    "mime_type",
    [mime_type for mime_type in MimeType if mime_type != MimeType.HTML] + [None],
)
def test_get_500(mime_type, generic_client, application_settings, gtaa_url, caplog):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f'{application_settings.get("BENG_DATA_DOMAIN")}gtaa/{DUMMY_IDENTIFIER}'
    CAT_TYPE = "program"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URL)
        if mime_type is MimeType.HTML:
            when(GTAAAPI)._get_lod_view_gtaa(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(None)
        else:
            when(GTAAAPI)._get_lod_gtaa(
                DUMMY_URL,
                mime_type,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(None)

        resp = generic_client.get(
            "offline",
            gtaa_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value if mime_type else None},
        )

        assert resp.status_code == 500

        if mime_type is None:
            assert "Error: No mime type detected" in resp.text.decode()
            assert "Not a proper mime type in the request." in caplog.text
        elif mime_type is MimeType.HTML:
            verify(GTAAAPI, times=1)._get_lod_view_gtaa(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            assert (
                "Could not generate an HTML view for this resource"
                in resp.text.decode()
            )
            assert (
                f"Could not generate HTML page for resource {DUMMY_URL}." in caplog.text
            )
        else:
            verify(GTAAAPI)._get_lod_gtaa(
                DUMMY_URL,
                mime_type,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            assert "Could not generate LOD for this resource" in resp.text.decode()
            assert f"Could not generate LOD for resource {DUMMY_URL}." in caplog.text

    finally:
        unstub()


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
# just tests the workflow
@pytest.mark.parametrize(
    "mime_type", [mime_type for mime_type in MimeType if mime_type != MimeType.HTML]
)
def test__get_lod_gtaa(mime_type, application_settings):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f'{application_settings.get("BENG_DATA_DOMAIN")}gtaa/{DUMMY_IDENTIFIER}'
    DUMMY_GRAPH = Graph()
    DUMMY_SERIALISED_GRAPH = (
        "just something pretending to be a serialisation of a graph"
    )
    gtaa_api = GTAAAPI()

    try:
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_GRAPH)
        when(DUMMY_GRAPH).serialize(format=mime_type.to_ld_format()).thenReturn(
            DUMMY_SERIALISED_GRAPH
        )
        serialised_graph = gtaa_api._get_lod_gtaa(
            DUMMY_URL,
            mime_type,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )
        verify(DUMMY_GRAPH, times=1).serialize(format=mime_type.to_ld_format())
        assert serialised_graph == DUMMY_SERIALISED_GRAPH

    finally:
        unstub()


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
@pytest.mark.skip(reason="the new 404 check prevents the verify from being run")
# just tests the workflow for an error
@pytest.mark.parametrize(
    "mime_type", [mime_type for mime_type in MimeType if mime_type != MimeType.HTML]
)
def test__get_lod_gtaa_error(mime_type, application_settings, caplog):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f'{application_settings.get("BENG_DATA_DOMAIN")}gtaa/{DUMMY_IDENTIFIER}'
    DUMMY_GRAPH = None
    gtaa_api = GTAAAPI()

    try:
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_GRAPH)
        serialised_graph = gtaa_api._get_lod_gtaa(
            DUMMY_URL,
            mime_type,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

        assert serialised_graph is None
        assert (
            f"Could not get the data for GTAA resource {DUMMY_URL} from triple store at {application_settings.get('SPARQL_ENDPOINT')}."
            in caplog.text
        )

    finally:
        unstub()


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
# inserts a real data graph to check serialisation
@pytest.mark.parametrize(
    "mime_type", [mime_type for mime_type in MimeType if mime_type != MimeType.HTML]
)
def test__get_lod_gtaa_with_data(mime_type, application_settings, i_gtaa_graph):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f'{application_settings.get("BENG_DATA_DOMAIN")}gtaa/{DUMMY_IDENTIFIER}'
    gtaa_api = GTAAAPI()

    try:
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(i_gtaa_graph)

        serialised_graph = gtaa_api._get_lod_gtaa(
            DUMMY_URL,
            mime_type,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

        try:
            g = Graph()
            g.parse(data=serialised_graph, format=mime_type.to_ld_format())
        except Exception:
            pytest.fail(f"Invalid {mime_type} output")

    finally:
        unstub()


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
def test__get_lod_view_gtaa(application, application_settings, i_gtaa_graph):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    gtaa_api = GTAAAPI()

    with (
        application.test_request_context()
    ):  # need to work within the app context as _get_lod_view_gtaa() uses the render_template() van Flask

        with (
            when(util.ld_util)
            .get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            .thenReturn(i_gtaa_graph)
        ):
            html_result = gtaa_api._get_lod_view_gtaa(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )

        assert html_result
        graph_json = json.loads(i_gtaa_graph.serialize(format="json-ld"))
        for item in graph_json:
            assert str(item["@id"]) in html_result


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
def test__get_lod_view_gtaa_error(application, application_settings, caplog):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    gtaa_api = GTAAAPI()

    with (
        application.test_request_context()
    ):  # need to work within the app context as _get_lod_view_gtaa() uses the render_template() van Flask

        with (
            when(util.ld_util)
            .get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            .thenReturn(None)
        ):
            html_result = gtaa_api._get_lod_view_gtaa(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )

        assert not html_result

        assert (
            f"Could not get the data for GTAA resource {DUMMY_URL} from triple store at {application_settings.get('SPARQL_ENDPOINT')}."
            in caplog.text
        )
