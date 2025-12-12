from rdflib import URIRef, Literal
from rdflib.namespace._RDF import RDF
from rdflib.namespace._SDO import SDO
from mockito import unstub
from util.lodview_util import (
    json_header_from_rdf_graph,
    json_iri_iri_from_rdf_graph,
    json_iri_lit_from_rdf_graph,
    json_iri_bnode_from_rdf_graph,
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
