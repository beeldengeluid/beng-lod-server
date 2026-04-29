import pytest
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, SKOS, SDO, DCTERMS  # type: ignore
from mockito import unstub
import util.lodview_util

DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"  # see setting_example.py
DUMMY_RESOURCE_ID = "1234"
DUMMY_RESOURCE_URI = f"{DUMMY_BENG_DATA_DOMAIN}id/scene/{DUMMY_RESOURCE_ID}"  # must be used in scene_rdf_xml.xml!


def test_json_header_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = util.lodview_util.json_header_from_rdf_graph(
            scene_rdf_graph, DUMMY_RESOURCE_URI
        )
        assert isinstance(ui_data, list)
        assert len(ui_data) == 1
        for ui_item in ui_data:
            assert all(x in ui_item for x in ["o", "title"])
            for ui_type_item in ui_item["o"]:
                assert all(
                    x in ui_type_item
                    for x in ["uri", "prefix", "namespace", "property"]
                )
                # there should be no RDF:type resources
                assert not (
                    ui_type_item["namespace"] == str(RDF)
                    and ui_type_item["property"] == "type"
                )
    finally:
        unstub()


def test_json_iri_iri_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = util.lodview_util.json_iri_iri_from_rdf_graph(
            scene_rdf_graph, DUMMY_RESOURCE_URI
        )
        assert isinstance(ui_data, list)
        assert len(ui_data) == 4
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])

            # all objects should be IRIs
            assert item["o"]["uri"].find("http") != -1
            assert all(
                x in item["p"] for x in ["uri", "prefix", "namespace", "property"]
            )
            assert all(
                x in item["o"]
                for x in [
                    "uri",
                    "prefix",
                    "namespace",
                    "property",
                    "labels",
                ]
            )
    finally:
        unstub()


def test_json_iri_lit_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = util.lodview_util.json_iri_lit_from_rdf_graph(
            scene_rdf_graph, DUMMY_RESOURCE_URI
        )
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
                    "labels",
                    "datatype",
                ]
            )

            # there should be no RDF:type resources
            assert not (
                item["p"]["namespace"] == str(RDF) and item["p"]["property"] == "type"
            )
    finally:
        unstub()


def test_json_iri_bnode_from_rdf_graph(program_rdf_graph_with_bnodes):
    try:
        # extract the IRI from the graph
        resource_iri_node = program_rdf_graph_with_bnodes.value(
            predicate=RDF.type, object=SDO.CreativeWork
        )
        resource_iri = str(resource_iri_node)
        # count the number of blank nodes as object value of the resource
        bnode_count_nodes = sum(
            1
            for p, o in program_rdf_graph_with_bnodes.predicate_objects(
                subject=URIRef(resource_iri)
            )
            if p != RDF.type and isinstance(o, BNode)
        )
        ui_data = util.lodview_util.json_iri_bnode_from_rdf_graph(
            program_rdf_graph_with_bnodes, resource_iri
        )
        assert isinstance(ui_data, list)
        assert len(ui_data) == bnode_count_nodes

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


def test_lod_view_resource_header(flask_test_client):
    """Given a flask_test_client, generate a header block for the lod view page.
    Test the output for some key elements.
    # TODO: This is a place holder for future split lod view generation
    """
    with flask_test_client.application.app_context():
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
        header = util.lodview_util.get_lod_view_resource_header(
            mock_header, "http://example.com"
        )
        print(header)


def test_get_lod_view_resource(
    flask_test_client,
    application_settings,
    program_rdf_graph,
):
    """Given an app context, generate a full HTML page for the lod view page.
    Test the output for some key elements.
    """
    with flask_test_client.application.app_context():
        resource_iri_node = program_rdf_graph.value(
            predicate=RDF.type, object=SDO.CreativeWork
        )
        resource_iri = str(resource_iri_node)
        title_node = program_rdf_graph.value(
            subject=resource_iri_node, predicate=SDO.name
        )
        html_content = util.lodview_util.get_lod_view_resource(
            program_rdf_graph,
            resource_iri,
            application_settings.get("SPARQL_ENDPOINT", ""),
        )
        assert "<!doctype html>" in html_content
        assert "<html" in html_content
        assert "</html>" in html_content
        assert (
            "LOD View" in html_content
        )  # assuming this text is present in the template

        lang_title = util.lodview_util.get_string_for_langstring(
            title_node, application_settings.get("UI_LANGUAGE_PREFERENCE", "nl")
        )
        assert f"<h1>{lang_title}</h1>" in html_content  # title should be in h1 tag
        resource_id_in_header = f"""<a class="link-light" title="&lt;{resource_iri}&gt;" href="{resource_iri}" target="_blank">&lt;{resource_iri}&gt;</a>"""
        assert resource_id_in_header in html_content  # resource IRI should be in header


@pytest.mark.parametrize(
    "iri,expected",
    [
        (
            "http://example.org/property",
            {
                "uri": "http://example.org/property",
                "prefix": "ex",
                "namespace": "http://example.org/",
                "property": "property",
            },
        ),
        (
            "http://example.org/",
            {
                "uri": "http://example.org/",
                "prefix": "",
                "namespace": "",
                "property": "",
            },
        ),
    ],
)
def test_json_parts_from_IRI(iri: str, expected: dict):
    """Deconstruct the given IRI into its parts and return them in a dict.
    The parts are prefix, namespace and property."""
    DUMMY_GRAPH = Graph()
    DUMMY_GRAPH.bind("ex", "http://example.org/")
    result = util.lodview_util.json_parts_from_IRI(DUMMY_GRAPH, iri)
    assert result == expected


@pytest.mark.parametrize(
    "label_type", [RDFS.label, SKOS.prefLabel, SDO.name, DCTERMS.title]
)
@pytest.mark.parametrize("lang", ["", "nl", "en"])
def test_json_label_for_node(label_type: URIRef, lang: str):
    """Generates a list of all possible labels for a given IRI or BNode.
    This list is used for the visualisation of the resource in the LOD view.
    :param lang: the language preference for the labels.
    """
    DUMMY_URI = URIRef("http://example.org/01")
    DUMMY_LITERAL = Literal("test", lang="nl")
    test_graph = Graph(bind_namespaces="core")
    test_graph.add((DUMMY_URI, label_type, DUMMY_LITERAL))
    result = util.lodview_util.json_label_for_node(test_graph, DUMMY_URI, lang)
    assert isinstance(result, list), "Apparently the wrong type is returned."
    for res in result:
        assert isinstance(res, str), "Apparently the wrong type is returned."
    if lang == "nl":
        assert result == ["test"], "Apparently the wrong label is returned."
    elif lang == "en":
        assert result == ["test @nl"], "Apparently the wrong label is returned."
    elif lang == "":
        assert result == ["test @nl"], "Apparently the wrong label is returned."
    else:
        assert result == ["test @nl"], "Apparently the wrong label is returned."


@pytest.mark.parametrize(
    "literal,lang,expected",
    [
        (Literal("test", lang="nl"), "nl", "test"),
        (Literal("test", lang="nl"), "en", "test @nl"),
        (Literal("test", lang="nl"), "", "test @nl"),
        (Literal("test"), "nl", "test"),
        (Literal("test"), "en", "test"),
        (Literal("test"), "", "test"),
    ],
)
def test_get_string_for_langstring(literal: Literal, lang: str, expected: str):
    """Tests the get_string_for_langstring function. Given a literal with or without
     a language tag, the function should return the string value of a literal, taking
    into account the language.
    """
    result = util.lodview_util.get_string_for_langstring(literal, lang)
    assert result == expected
