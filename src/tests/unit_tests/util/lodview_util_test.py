import pytest
from rdflib import URIRef, Literal, Graph
from rdflib.namespace._RDF import RDF
from rdflib.namespace._SDO import SDO
from mockito import unstub
from util.lodview_util import (
    json_header_from_rdf_graph,
    json_iri_iri_from_rdf_graph,
    json_iri_lit_from_rdf_graph,
    json_iri_bnode_from_rdf_graph,
    get_lod_view_resource_header,
    get_lod_view_resource,
)

DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"  # see setting_example.py
DUMMY_RESOURCE_ID = "1234"
DUMMY_RESOURCE_URI = f"{DUMMY_BENG_DATA_DOMAIN}id/scene/{DUMMY_RESOURCE_ID}"  # must be used in scene_rdf_xml.xml!


def test_json_header_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_header_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert isinstance(ui_data, list)
        assert len(ui_data) == 1
        # assert "o" in ui_data[0]
        assert all(x in ui_data[0] for x in ["o", "title"])
        assert all(
            x in ui_data[0]["o"] for x in ["uri", "prefix", "namespace", "property"]
        )

        # only schema.org types (SDO) types are returned
        assert ui_data[0]["o"]["uri"] == f"{str(SDO)}Clip"
        assert ui_data[0]["o"]["namespace"] == str(SDO)
        assert ui_data[0]["o"]["property"] == "Clip"

    finally:
        unstub()


def test_json_iri_iri_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_iri_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert isinstance(ui_data, list)
        assert len(ui_data) == 2
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            # there should be no RDF:type resources
            assert not (
                item["p"]["namespace"] == str(RDF) and item["p"]["property"] == "type"
            )
            # all objects should be IRIs
            assert item["o"]["uri"].find("http") != -1
            assert all(
                x in ui_data[0]["p"] for x in ["uri", "prefix", "namespace", "property"]
            )
            assert all(
                x in ui_data[0]["o"]
                for x in [
                    "uri",
                    "literal_form",
                    "prefix",
                    "namespace",
                    "property",
                    "pref_label",
                ]
            )

    finally:
        unstub()


def test_json_iri_lit_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_lit_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert isinstance(ui_data, list)
        assert len(ui_data) == 1
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            assert all(
                x in item["p"] for x in ["uri", "prefix", "namespace", "property"]
            )
            assert all(
                x in item["o"]
                for x in [
                    "literal_value",
                    "datatype",
                    "datatype_prefix",
                    "datatype_namespace",
                    "datatype_property",
                ]
            )

            # there should be no RDF:type resources
            assert not (
                item["p"]["namespace"] == str(RDF) and item["p"]["property"] == "type"
            )
            assert (
                item["o"]["literal_value"].find("http") == -1
            )  # all objects should be Literals
    finally:
        unstub()


@pytest.mark.skip(reason="Test is not correct with dummy URL")
def test_json_iri_bnode_from_rdf_graph(program_rdf_graph_with_bnodes):
    try:
        ui_data = json_iri_bnode_from_rdf_graph(
            program_rdf_graph_with_bnodes, DUMMY_RESOURCE_URI
        )
        assert isinstance(ui_data, list)
        assert len(ui_data) == 31
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            assert all(
                x in item["p"] for x in ["uri", "prefix", "namespace", "property"]
            )

            for bnode_content in item["o"]:
                assert isinstance(bnode_content, dict)
                assert all(x in bnode_content for x in ["pred", "obj"])
                assert all(
                    x in bnode_content["pred"]
                    for x in ["uri", "prefix", "namespace", "property"]
                )
                assert isinstance(bnode_content["obj"], str) or isinstance(
                    bnode_content["obj"], dict
                )
                if isinstance(bnode_content["obj"], dict):
                    if isinstance(bnode_content, URIRef):
                        assert all(
                            x in bnode_content["obj"]
                            for x in [
                                "uri",
                                "prefix",
                                "namespace",
                                "property",
                                "pref_label",
                            ]
                        )
                    if isinstance(bnode_content, Literal):
                        assert all(x in bnode_content["obj"] for x in ["label"])

    finally:
        unstub()


def test_lod_view_resource_header(application):
    """Given an app context, generate a gheader block for the lod view page.
    Test the output for some key elements.
    # TODO: This is a place holder for future split lod view generation
    """
    with application.app_context():
        mock_header = [
            {
                "title": "my title",
                "o": {
                    "uri": "http://example.com",
                    "prefix": "http://schema.org/",
                    "namespace": "",
                    "property": "",
                },
            }
        ]
        header = get_lod_view_resource_header(mock_header)
        print(header)


@pytest.mark.skip(reason="Test fails because urlfor doesn't work.")
def test_get_lod_view_resource(
    application,
    application_settings,
    program_rdf_graph,
):
    """Given an app context, generate a full HTML page for the lod view page.
    Test the output for some key elements.
    """
    with application.app_context():
        resource_iri_node = program_rdf_graph.value(
            predicate=RDF.type, object=SDO.CreativeWork
        )
        resource_iri = str(resource_iri_node)
        title_node = program_rdf_graph.value(
            subject=resource_iri_node, predicate=SDO.name
        )
        html_content = get_lod_view_resource(
            program_rdf_graph,
            resource_iri,
            application_settings.get("SPARQL_ENDPOINT", ""),
        )
        # resp.text.decode("utf-8")
        assert "<!doctype html>" in html_content
        assert "<html" in html_content
        assert "</html>" in html_content
        assert (
            "LOD View" in html_content
        )  # assuming this text is present in the template

        title = str(title_node)
        assert f"<h1>{title}</h1>" in html_content  # title should be in h1 tag
        resource_id_in_header = f"""<a class="link-light" title="&lt;{resource_iri}&gt;" href="{resource_iri}" target="_blank">&lt;{resource_iri}&gt;</a>"""
        assert resource_id_in_header in html_content  # resource IRI should be in header
