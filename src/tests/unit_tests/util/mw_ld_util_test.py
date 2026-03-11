import pytest
from rdflib.compare import graph_diff, isomorphic


def test_equivalence(rdf_from_ld_util, rdf_from_mw_ld_util):
    """Compare graph loaded with RDF for resource using ld_util module
    with graph containing RDF for resource from mw_ld_util module.
    Use graph_diff(g1: Graph, g2: Graph) -> Tuple[Graph, Graph, Graph]:
    Returns three sets of triples: "in both", "in first" and "in second"."
    """
    if not isomorphic(rdf_from_ld_util, rdf_from_mw_ld_util):
        diff = graph_diff(rdf_from_ld_util, rdf_from_mw_ld_util)
        print("Graphs are not isomorphic.")
        print("Triples in both graphs:")
        for t in diff[0]:
            print(t)
        print("Triples in first graph but not in second:")
        for t in diff[1]:
            print(t)
        print("Triples in second graph but not in first:")
        for t in diff[2]:
            print(t)
    assert isomorphic(rdf_from_ld_util, rdf_from_mw_ld_util)


@pytest.mark.parametrize(
    "subgraph",
    [
        "part_of_program",
        "parent",
        "entities_and_roles",
        "preflabels_and_type",
        "is_part_of_relation",
        "blank_node",
        "lod_resource",
    ],
    indirect=True,
)
def test_subgraph_is_included(subgraph, rdf_from_mw_ld_util):
    """This test checks if the subgraph of triples returned by each
    construct query in ld_util is included in the graph returned by mw_ld_util.
    Note that the subgraph param is a fixture that returns the graph for
    the specific construct query.
    NB: graph_diff returns in_both, in_first, in_second
    """
    diff = graph_diff(subgraph, rdf_from_mw_ld_util)
    if len(subgraph) > 0:
        assert (
            len(diff[1]) == 0
        ), f"Subgraph contains triples not in mw_ld_util graph: {diff[1]}"
    else:
        print("Subgraph is empty, cannot compare.")
        assert True


# TODO: A test collection could be a subdirectory per resource type,
# containing a few resources of that type.
# data/programs/2102501280372629231
# data/programs/2102501280372628531
# data/series/
# data/gtaa/concept/100390
# data/Link/HFX0244
