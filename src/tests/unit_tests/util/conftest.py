import pytest

@pytest.fixture()
def scene_rdf_xml(open_file):
    """Returns an example RDF/XML of a scene"""
    return open_file(__file__, "scene_rdf_xml.xml")