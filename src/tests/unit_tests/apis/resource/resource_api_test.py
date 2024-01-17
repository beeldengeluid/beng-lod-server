import json
import pytest

from mockito import when, unstub, verify, ANY
from rdflib import Graph

import util.ld_util 

from apis.resource.resource_api import ResourceAPI
from models.ResourceURILevel import ResourceURILevel
from util.mime_type_util import MimeType

def test_init():
    resource_api = ResourceAPI()
    assert isinstance(resource_api, ResourceAPI)



@pytest.mark.parametrize('mime_type',[
MimeType.JSON_LD,
MimeType.HTML
])
def test_get_200(mime_type, generic_client, application_settings, resource_query_url):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "just something pretending to be an HTML page"
    DUMMY_GRAPH = Graph()
    DUMMY_SERIALISED_GRAPH = "just something pretending to be a serialisation of a graph"
    CAT_TYPE = "program"

    try:
        when(util.ld_util).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, application_settings.get("BENG_DATA_DOMAIN")).thenReturn(DUMMY_URL)
        if mime_type is MimeType.HTML:
            when(ResourceAPI)._get_lod_view_resource(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION")).thenReturn(DUMMY_PAGE)
        else:
            when(util.ld_util).get_lod_resource_from_rdf_store(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION")).thenReturn(DUMMY_GRAPH)
            when(DUMMY_GRAPH).serialize(format=mime_type).thenReturn(DUMMY_SERIALISED_GRAPH)

        generic_client.get("offline", resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER), headers={"Accept": mime_type.value})

        verify(util.ld_util, times=1).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, application_settings.get("BENG_DATA_DOMAIN"))
        if mime_type is MimeType.HTML:
            verify(ResourceAPI, times=1)._get_lod_view_resource(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION"))
        else:
            verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION"))
            verify(DUMMY_GRAPH, times=1).serialize(format=mime_type)
    finally:
        unstub()

@pytest.mark.parametrize("cause", [
    "no_mime_type",
    "generate_uri_failed"
])
def test_get_400(cause, generic_client, application_settings, resource_query_url):
    DUMMY_IDENTIFIER = 1234
    CAT_TYPE = "program"

    if cause == "no_mime_type":
        BAD_MIME_TYPE = None
        response = generic_client.get("offline", resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER), headers={"Accept": BAD_MIME_TYPE})
        assert response.status_code == 400

    elif cause == "generate_uri_failed":
        DUMMY_MIME_TYPE = "dummy mime type"
        with when(util.ld_util).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, application_settings.get("BENG_DATA_DOMAIN")).thenRaise(ValueError):
            response = generic_client.get("offline", resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER), headers={"Accept": DUMMY_MIME_TYPE})
            assert response.status_code == 400
    else:
        raise ValueError("Bad test variable")


@pytest.mark.parametrize('mime_type, cause',[
(MimeType.JSON_LD, "not_rdf_graph"),
(MimeType.JSON_LD, "no_serialized_graph"),
(MimeType.HTML, "no_html_page"),
])
def test_get_500(mime_type, cause, generic_client, application_settings, resource_query_url):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    DUMMY_GRAPH = Graph()
    CAT_TYPE = "program"

    try:
        when(util.ld_util).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, application_settings.get("BENG_DATA_DOMAIN")).thenReturn(DUMMY_URL)
        if mime_type is MimeType.HTML and cause == "no_html_page":
            when(ResourceAPI)._get_lod_view_resource(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION")).thenReturn(None)
        elif mime_type is MimeType.JSON_LD and cause == "not_rdf_graph":
            when(util.ld_util).get_lod_resource_from_rdf_store(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION")).thenReturn(None)
            when(DUMMY_GRAPH).serialize(format=mime_type).thenReturn(None)  # shouldn't be called, but we want to check this
        elif mime_type is MimeType.JSON_LD and cause == "no_serialized_graph":
            when(util.ld_util).get_lod_resource_from_rdf_store(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION")).thenReturn(DUMMY_GRAPH)
            when(DUMMY_GRAPH).serialize(format=mime_type).thenReturn(None)

        response = generic_client.get("offline", resource_query_url(CAT_TYPE, DUMMY_IDENTIFIER), headers={"Accept": mime_type.value})

        verify(util.ld_util, times=1).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, application_settings.get("BENG_DATA_DOMAIN"))

        assert response.status_code == 500

        if mime_type is MimeType.HTML:
            verify(ResourceAPI, times=1)._get_lod_view_resource(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION"))
            if cause == "no_html_page":
                assert "Could not generate an HTML view for this resource" in str(response.text)
        else:
            verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION"))
            verify(DUMMY_GRAPH, times=0 if cause == "not_rdf_graph" else 1).serialize(format=mime_type)
            if cause == "not_rdf_graph":
                assert "No graph created" in str(response.text)
            elif cause == "no_serialized_graph":
                assert "Serialisation failed" in str(response.text)
    finally:
        unstub()

@pytest.mark.parametrize('item_type', [
    None,
    "scene",
    "program",
    "season",
    "series"
])
def test__get_lod_view_resource(item_type, application, application_settings, i_scene_graph, i_program_graph, i_season_graph, i_series_graph):
    DUMMY_IDENTIFIER = "dummy-identifier"
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    resource_api = ResourceAPI()

    with application.test_request_context():  # need to work within the app context as get_lod_view_resource() uses the render_template() van Flask
        if item_type:
            test_graph = locals()[f"i_{item_type}_graph"]
        else:
            test_graph = None

        with when(util.ld_util).get_lod_resource_from_rdf_store(
                DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION")
            ).thenReturn(test_graph):
            html_result = resource_api._get_lod_view_resource(DUMMY_URL, application_settings.get("SPARQL_ENDPOINT"), application_settings.get("URI_NISV_ORGANISATION"))

        if item_type:
            assert html_result
            graph_json = json.loads(test_graph.serialize(format="json-ld"))
            for item in graph_json:
                assert str(item["@id"]) in html_result
        else:
            assert not html_result