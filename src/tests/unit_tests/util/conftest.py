import pytest
from rdflib import Graph


@pytest.fixture()
def scene_rdf_xml(open_file):
    """Returns an example RDF/XML of a scene"""
    return open_file(__file__, "scene_rdf_xml.xml")


@pytest.fixture()
def scene_rdf_graph(scene_rdf_xml):
    g = Graph()
    g.parse(data=scene_rdf_xml, format="xml")
    return g


@pytest.fixture()
def program_json_ld(open_file):
    """Returns an example JSON-LD of a program"""
    return open_file(__file__, "response_1654249468282.json")


@pytest.fixture()
def program_rdf_graph_with_bnodes(program_json_ld):
    g = Graph()
    g.parse(data=program_json_ld, format="json-ld")
    return g


@pytest.fixture()
def program_rdf_xml(open_file):
    """Returns an example RDF/XML of a program"""
    return open_file(__file__, "sparql_response_program_2101712160234752431.xml")
