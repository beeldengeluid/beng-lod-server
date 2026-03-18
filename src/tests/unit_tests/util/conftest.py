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
def query_results_select(open_file):
    """Returns SPARQL result in JSON format"""
    return open_file(__file__, "sparql_results_select_query.json")


@pytest.fixture()
def program_json_ld(open_file):
    """Returns an example JSON-LD of a program"""
    return open_file(__file__, "rdf_graph_program_2101608060047830331.json")


@pytest.fixture()
def program_rdf_graph_with_bnodes(program_json_ld):
    g = Graph()
    g.parse(data=program_json_ld, format="json-ld")
    return g


@pytest.fixture()
def program_rdf_xml(open_file):
    """Returns an example RDF/XML of a program"""
    return open_file(__file__, "sparql_response_program_2101712160234752431.xml")


@pytest.fixture()
def program_rdf_graph(load_file_as_graph):
    """Returns graph of an example NISV program in JSON-LD."""
    return load_file_as_graph(__file__, "rdf_graph_program_2101608060047830331.json")


@pytest.fixture()
def program_12_entity_problem_xml(open_file):
    """Returns an example RDF/XML of a program with entity/DTD problem."""
    return open_file(__file__, "program_12_entity_problem.xml")


@pytest.fixture()
def program_12_parsing_ok_xml(open_file):
    """Returns RDF/XML of a program where the entity/DTD problem doesn't occur."""
    return open_file(__file__, "program_12_parsing_ok.xml")


@pytest.fixture()
def rdf_from_ld_util(load_file_as_graph):
    """Returns RDF graph of a program from the ld_util function."""
    return load_file_as_graph(
        __file__, "ldutil_compare_program_2102501280372631431.ttl"
    )


@pytest.fixture()
def rdf_from_mw_ld_util(load_file_as_graph):
    """Returns RDF graph of a program from the mw_ld_util function."""
    return load_file_as_graph(
        __file__, "mw_ldutil_compare_program_2102501280372631431.ttl"
    )
