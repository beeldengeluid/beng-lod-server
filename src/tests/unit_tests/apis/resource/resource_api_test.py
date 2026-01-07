import json
import pytest
from flask import Response
from mockito import when, unstub, verify
from rdflib import Graph, URIRef
from rdflib.namespace._RDF import RDF
from rdflib.namespace._SDO import SDO
from rdflib.compare import to_isomorphic
from apis.resource.resource_api import ResourceAPI
from models.ResourceApiUriLevel import ResourceApiUriLevel
import util.ld_util
from util.mime_type_util import MimeType
import util.lodview_util


def test_init():
    resource_api = ResourceAPI()
    assert isinstance(resource_api, ResourceAPI)


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200(
    mime_type,
    generic_client,
    application_settings,
    i_program_graph_2,
):
    """Given a flask test client, application settings, mime_type and a fixture for
    a program, a request is handled and the response is tested."""

    CAT_TYPE = "program"
    IDENTIFIER = "123456"
    PATH = f"/id/{CAT_TYPE}/{IDENTIFIER}"
    # get the URL from the fixture
    URL_NODE = i_program_graph_2.value(predicate=RDF.type, object=SDO.CreativeWork)
    URL = str(URL_NODE)

    try:
        # stub the invocations
        when(ResourceAPI).check_for_wemi_postfix(IDENTIFIER).thenReturn(
            (200, IDENTIFIER)
        )
        when(util.ld_util).generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN", ""),
        ).thenReturn(URL)
        when(util.ld_util).is_nisv_cat_resource(
            URL, application_settings.get("SPARQL_ENDPOINT", "")
        ).thenReturn(True)
        when(util.ld_util).get_lod_resource_from_rdf_store(
            URL,
            application_settings.get("SPARQL_ENDPOINT", ""),
            application_settings.get("URI_NISV_ORGANISATION", ""),
        ).thenReturn(
            i_program_graph_2
        )  # invocation returns Graph object from fixture

        # do the actual request
        resp = generic_client.get(
            "offline",
            PATH,
            headers={"Accept": mime_type.value},
        )
        assert resp.status_code == 200

        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            URL,
            application_settings.get("SPARQL_ENDPOINT", ""),
            application_settings.get("URI_NISV_ORGANISATION", ""),
        )

        # test what comes out
        if mime_type is MimeType.HTML:
            html_content = resp.text.decode("utf-8")
            assert "<!doctype html>" in html_content
            assert "<html" in html_content
            assert "</html>" in html_content
            assert (
                "LOD View" in html_content
            )  # assuming this text is present in the template

            resource_iri_node = i_program_graph_2.value(
                predicate=RDF.type, object=SDO.CreativeWork
            )
            resource_iri = str(resource_iri_node)
            title_node = i_program_graph_2.value(
                subject=resource_iri_node, predicate=SDO.name
            )
            title = str(title_node)
            assert f"<h1>{title}</h1>" in html_content  # title should be in h1 tag
            resource_id_in_header = f"""<a class="link-light" title="&lt;{resource_iri}&gt;" href="{resource_iri}" target="_blank">&lt;{resource_iri}&gt;</a>"""
            assert (
                resource_id_in_header in html_content
            )  # resource IRI should be in header

        else:
            g = Graph()
            try:
                g.parse(data=resp.text, format=mime_type.to_ld_format())
            except Exception:
                pytest.fail(f"Invalid {mime_type} output")
            iso1 = to_isomorphic(i_program_graph_2)
            iso2 = to_isomorphic(g)
            assert iso1 == iso2

    finally:
        unstub()


def test_get_200_mime_type_none(
    generic_client, application_settings, resource_query_url
):
    """Given a generic client and application settings, send a get request
    with no mime_type. Test that the response is what is expected (default mime_type).
    """
    # """Tests the default behaviour for the mime type, which is currently to set it to JSON-LD if the input is None"""
    DUMMY_IDENTIFIER = "1234"
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_GRAPH = Graph(bind_namespaces="core")
    DUMMY_GRAPH.add((URIRef(DUMMY_URL), RDF.type, SDO.CreativeWork))
    DUMMY_SERIALISED_GRAPH = DUMMY_GRAPH.serialize(
        format=MimeType.JSON_LD.to_ld_format(), auto_compact=True
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
        when(util.ld_util).is_nisv_cat_resource(
            DUMMY_URL, application_settings.get("SPARQL_ENDPOINT", "")
        ).thenReturn(True)
        when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_GRAPH)

        if default_mimetype is MimeType.HTML:
            when(util.lodview_util).generate_html_page(
                DUMMY_GRAPH,
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
            ).thenReturn(Response(DUMMY_PAGE, mimetype=MimeType.HTML.value))
        else:
            when(util.lodview_util).get_serialised_graph(
                DUMMY_GRAPH, default_mimetype
            ).thenReturn(
                Response(
                    DUMMY_SERIALISED_GRAPH, mimetype=default_mimetype.value, status=200
                )
            )

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
        verify(util.ld_util, times=1).is_nisv_cat_resource(
            DUMMY_URL, application_settings.get("SPARQL_ENDPOINT", "")
        )
        verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

        if default_mimetype is MimeType.HTML:
            verify(util.lodview_util, times=1).generate_html_page(
                DUMMY_GRAPH,
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
            )
            assert resp.text.decode() == DUMMY_PAGE
        else:
            verify(util.lodview_util, times=1).get_serialised_graph(
                DUMMY_GRAPH, default_mimetype
            )
            assert resp.text.decode("utf-8") == DUMMY_SERIALISED_GRAPH

    finally:
        unstub()


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
@pytest.mark.skip(
    reason="test needs to be updated because the identifier is now validated."
)
@pytest.mark.parametrize("wemi_entity", ["work", "manifestation", "expression"])
def test_get_302(generic_client, application_settings, resource_query_url, wemi_entity):
    DUMMY_IDENTIFIER = "1234"
    DUMMY_URL = f"http://{DUMMY_IDENTIFIER}"
    CAT_TYPE = "program"
    DUMMY_WEMI_IDENTIFIER = f"{DUMMY_IDENTIFIER}_{wemi_entity}"

    with (
        when(util.ld_util)
        .generate_lod_resource_uri(
            ResourceApiUriLevel(CAT_TYPE),
            DUMMY_IDENTIFIER,
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        .thenReturn(DUMMY_URL)
    ):
        response = generic_client.get(
            "offline",
            resource_query_url(CAT_TYPE, DUMMY_WEMI_IDENTIFIER),
        )
        assert response.status_code == 302
        assert response.headers["location"] == DUMMY_URL


@pytest.mark.parametrize(
    "wemi_entity", ["blabla", "some stuff with space and _ underscore etc."]
)
def test_get_400_wemi(
    generic_client, application_settings, resource_query_url, wemi_entity
):
    DUMMY_IDENTIFIER = "1234"
    CAT_TYPE = "program"
    DUMMY_WEMI_IDENTIFIER = f"{DUMMY_IDENTIFIER}_{wemi_entity}"

    response = generic_client.get(
        "offline",
        resource_query_url(CAT_TYPE, DUMMY_WEMI_IDENTIFIER),
    )
    assert response.status_code == 400


def test_get_400(generic_client, application_settings, resource_query_url):
    DUMMY_IDENTIFIER = "1234"
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


@pytest.mark.skip(reason="lodview is moved to util. test functions need to be updated.")
@pytest.mark.skip(reason="test needs to be updated because some resources get 404")
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
    DUMMY_IDENTIFIER = "1234"
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
@pytest.mark.parametrize("item_type", ["scene", "program", "season", "series"])
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
        test_graph = locals()[f"i_{item_type}_graph"]

        with (
            when(util.ld_util)
            .get_lod_resource_from_rdf_store(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )
            .thenReturn(test_graph)
        ):
            html_result = util.lodview_util.get_lod_view_resource(
                test_graph,
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT", ""),
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
