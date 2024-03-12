import json
import pytest

from mockito import when, unstub, verify
from rdflib import Graph

import util.ld_util

from apis.resource.resource_api import ResourceAPI
from models.ResourceApiUriLevel import ResourceApiUriLevel
from util.mime_type_util import MimeType


def test_init():
    resource_api = ResourceAPI()
    assert isinstance(resource_api, ResourceAPI)


# Just tests the flow
@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200(mime_type, generic_client, application_settings, resource_query_url):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_GRAPH = Graph()
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
            when(ResourceAPI)._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(DUMMY_PAGE)
        else:
            when(util.ld_util).get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(DUMMY_GRAPH)
            when(DUMMY_GRAPH).serialize(
                format=mime_type.to_ld_format(), auto_compact=True
            ).thenReturn(DUMMY_SERIALISED_GRAPH)

        resp = generic_client.get(
            "offline",
            resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        if mime_type is MimeType.HTML:
            verify(ResourceAPI, times=1)._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            assert resp.text.decode() == DUMMY_PAGE
        else:
            verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            verify(DUMMY_GRAPH, times=1).serialize(
                format=mime_type.to_ld_format(), auto_compact=True
            )
            assert resp.text.decode() == DUMMY_SERIALISED_GRAPH

    finally:
        unstub()


# Just tests the flow
def test_get_200_mime_type_none(
    generic_client, application_settings, resource_query_url
):
    """Tests the default behaviour for the mime type, which is currently to set it to JSON-LD if the input is None"""
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_GRAPH = Graph()
    DUMMY_SERIALISED_GRAPH = (
        "just something pretending to be a serialisation of a graph"
    )
    CAT_TYPE = "program"
    input_mime_type = None
    default_mimetype = MimeType.JSON_LD

    try:
        when(util.ld_util).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URL)

        if default_mimetype is MimeType.HTML:
            when(ResourceAPI)._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(DUMMY_PAGE)
        else:
            when(util.ld_util).get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(DUMMY_GRAPH)
            when(DUMMY_GRAPH).serialize(
                format=default_mimetype.to_ld_format(), auto_compact=True
            ).thenReturn(DUMMY_SERIALISED_GRAPH)

        resp = generic_client.get(
            "offline",
            resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": input_mime_type},
        )

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        if default_mimetype is MimeType.HTML:
            verify(ResourceAPI, times=1)._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            assert resp.text.decode() == DUMMY_PAGE
        else:
            verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            verify(DUMMY_GRAPH, times=1).serialize(
                format=default_mimetype.to_ld_format(), auto_compact=True
            )
            assert resp.text.decode() == DUMMY_SERIALISED_GRAPH

    finally:
        unstub()


# inserts a real data graph to check the conversions to the right format
@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200_with_data(
    mime_type, generic_client, application_settings, resource_query_url, i_program_graph
):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    CAT_TYPE = "program"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URL)
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(i_program_graph)

        resp = generic_client.get(
            "offline",
            resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
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


def test_get_400(generic_client, application_settings, resource_query_url):
    DUMMY_IDENTIFIER = 1234
    CAT_TYPE = "program"
    DUMMY_MIME_TYPE = "dummy mime type"

    with (
        when(util.ld_util)
        .generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        .thenRaise(ValueError)
    ):
        response = generic_client.get(
            "offline",
            resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": DUMMY_MIME_TYPE},
        )
        assert response.status_code == 400


@pytest.mark.parametrize(
    "mime_type, cause",
    [
        (MimeType.JSON_LD, "not_rdf_graph"),
        (MimeType.JSON_LD, "no_serialized_graph"),
        (MimeType.HTML, "no_html_page"),
    ],
)
def test_get_500(
    mime_type, cause, generic_client, application_settings, resource_query_url
):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    DUMMY_GRAPH = Graph()
    CAT_TYPE = "program"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URL)
        if mime_type is MimeType.HTML and cause == "no_html_page":
            when(ResourceAPI)._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(None)
        elif mime_type is MimeType.JSON_LD and cause == "not_rdf_graph":
            when(util.ld_util).get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(None)
            when(DUMMY_GRAPH).serialize(
                format=mime_type.to_ld_format(), auto_compact=True
            ).thenReturn(
                None
            )  # shouldn't be called, but we want to check this
        elif mime_type is MimeType.JSON_LD and cause == "no_serialized_graph":
            when(util.ld_util).get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            ).thenReturn(DUMMY_GRAPH)
            when(DUMMY_GRAPH).serialize(
                format=mime_type.to_ld_format(), auto_compact=True
            ).thenReturn(None)

        response = generic_client.get(
            "offline",
            resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        )

        assert response.status_code == 500

        if mime_type is MimeType.HTML:
            verify(ResourceAPI, times=1)._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            if cause == "no_html_page":
                assert "Could not generate an HTML view for this resource" in str(
                    response.text
                )
        else:
            verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            verify(DUMMY_GRAPH, times=0 if cause == "not_rdf_graph" else 1).serialize(
                format=mime_type.to_ld_format(), auto_compact=True
            )
            if cause == "not_rdf_graph":
                assert "No graph created" in str(response.text)
            elif cause == "no_serialized_graph":
                assert "Serialisation failed" in str(response.text)
    finally:
        unstub()


# Note: it may appear as if the graph arguments are not used. But this is not true, they are loaded dynamically
# according to the program type
@pytest.mark.parametrize("item_type", [None, "scene", "program", "season", "series"])
def test__get_lod_view_resource(
    item_type,
    application,
    application_settings,
    i_scene_graph,
    i_program_graph,
    i_season_graph,
    i_series_graph,
):
    DUMMY_IDENTIFIER = "dummy-identifier"
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    resource_api = ResourceAPI()

    with (
        application.test_request_context()
    ):  # need to work within the app context as get_lod_view_resource() uses the render_template() van Flask
        if item_type:
            test_graph = locals()[f"i_{item_type}_graph"]
        else:
            test_graph = None

        with (
            when(util.ld_util)
            .get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            .thenReturn(test_graph)
        ):
            html_result = resource_api._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )

            if item_type:
                assert html_result
                assert html_result.startswith("<!doctype html>")
                assert html_result.endswith("</html>")

                graph_json = json.loads(
                    test_graph.serialize(format="json-ld", auto_compact=True)
                )
                if "@graph" in graph_json:
                    for item in graph_json["@graph"]:
                        if item["@id"].startswith("gtaa:"):
                            assert (
                                str(item["@id"]).replace(
                                    "gtaa:", "http://data.beeldengeluid.nl/gtaa/"
                                )
                                in html_result
                            )
                        else:
                            assert str(item["@id"]) in html_result
                else:
                    for item in graph_json:
                        if item == "@id":
                            assert str(graph_json["@id"]) in html_result
                        elif "@id" in item:
                            assert str(item["@id"]) in html_result

            else:
                assert not html_result
