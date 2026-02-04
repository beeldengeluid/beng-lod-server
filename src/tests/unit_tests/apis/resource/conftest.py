import pytest


@pytest.fixture(scope="module")
def resource_query_url():
    def genResourceURL(type, identifier):
        return f"/id/{type}/{identifier}"

    return genResourceURL


@pytest.fixture()
def o_get_schema(open_file):
    """Returns an example version of the schema."""
    return open_file(__file__, "output_get_schema.ttl")


@pytest.fixture()
def i_scene_graph(load_file_as_graph):
    """Returns graph of an example NISV scene in JSON-LD."""
    return load_file_as_graph(__file__, "rdf_scene_1635932280680.json")


@pytest.fixture()
def i_program_graph(load_file_as_graph):
    """Returns graph of an example NISV program in JSON-LD."""
    return load_file_as_graph(__file__, "rdf_program_1635930242168.json")


@pytest.fixture()
def i_program_graph_2(load_file_as_graph):
    """Returns graph of an example NISV program in JSON-LD."""
    return load_file_as_graph(__file__, "rdf_program_2101608050034634431.json")


@pytest.fixture()
def i_season_graph(load_file_as_graph):
    """Returns graph of an example NISV season in JSON-LD."""
    return load_file_as_graph(__file__, "rdf_season_1635930556031.json")


@pytest.fixture()
def i_series_graph(load_file_as_graph):
    """Returns graph of an example NISV series in JSON-LD."""
    return load_file_as_graph(__file__, "rdf_series_1635930663729.json")


@pytest.fixture()
def graph_from_rdf_store(load_file_as_graph):
    """Returns a graph with RDF of an NISV program."""
    return load_file_as_graph(__file__, "rdf_program_2101608050034634431.ttl")
