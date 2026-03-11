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


# fixtures for get_rdf_resource comparison tests
#
@pytest.fixture()
def label_for_is_part_of_program(load_file_as_graph):
    """Returns RDF graph returned by partial ld_util function for isPartOfProgram."""
    return load_file_as_graph(__file__, "test_label_for_is_part_of_program.ttl")


@pytest.fixture()
def label_for_parent(load_file_as_graph):
    """Returns RDF graph returned by partial ld_util function for parent."""
    return load_file_as_graph(__file__, "test_label_for_parent.ttl")


@pytest.fixture()
def label_triples_and_types_for_entities_and_roles(load_file_as_graph):
    """Returns RDF graph returned by partial ld_util function for label triples
    and types for entities and roles."""
    return load_file_as_graph(
        __file__, "test_label_triples_and_types_for_entities_and_roles.ttl"
    )


@pytest.fixture()
def preflabels_and_type_for_lod_resource(load_file_as_graph):
    """Returns RDF graph returned by partial ld_util function for preflabel triples
    and types."""
    return load_file_as_graph(__file__, "test_preflabels_and_type_for_lod_resource.ttl")


@pytest.fixture()
def triple_for_is_part_of_relation(load_file_as_graph):
    """Returns RDF graph returned by partial ld_util function for isPartOf relation."""
    return load_file_as_graph(__file__, "test_triple_for_is_part_of_relation.ttl")


@pytest.fixture()
def triple_for_blank_node(load_file_as_graph):
    """Returns RDF graph returned by partial ld_util function for blank node triples."""
    return load_file_as_graph(__file__, "test_triples_for_blank_node.ttl")


@pytest.fixture()
def triple_for_lod_resource(load_file_as_graph):
    """Returns RDF graph returned by partial ld_util function for LOD resource triples."""
    return load_file_as_graph(__file__, "test_triples_for_lod_resource.ttl")


@pytest.fixture
def subgraph(
    request,
    label_for_is_part_of_program,
    label_for_parent,
    label_triples_and_types_for_entities_and_roles,
    preflabels_and_type_for_lod_resource,
    triple_for_is_part_of_relation,
    triple_for_blank_node,
    triple_for_lod_resource,
):
    type = request.param

    if type == "part_of_program":
        return label_for_is_part_of_program
    elif type == "parent":
        return label_for_parent
    elif type == "entities_and_roles":
        return label_triples_and_types_for_entities_and_roles
    elif type == "preflabels_and_type":
        return preflabels_and_type_for_lod_resource
    elif type == "is_part_of_relation":
        return triple_for_is_part_of_relation
    elif type == "blank_node":
        return triple_for_blank_node
    elif type == "lod_resource":
        return triple_for_lod_resource
    else:
        raise ValueError("unknown type")
