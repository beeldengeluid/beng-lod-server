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