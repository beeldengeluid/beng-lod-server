import pytest

@pytest.fixture()
def o_get_schema(open_file):
    """Returns an example version of the schema."""
    return open_file(__file__, "output_get_schema.ttl")

@pytest.fixture()
def i_ob_scene_rdf(load_json_file):
    """Returns RDF of an example Open Beelden item in JSON-LD."""
    return load_json_file(__file__, "rdf_ob_scene_2101703040124290024.json")

@pytest.fixture()
def i_scene_graph(load_json_file_as_graph):
    """Returns graph of an example NISV scene in JSON-LD."""
    return load_json_file_as_graph(__file__, "rdf_scene_1635932280680.json")

@pytest.fixture()
def i_program_graph(load_json_file_as_graph):
    """Returns graph of an example NISV program in JSON-LD."""
    return load_json_file_as_graph(__file__, "rdf_program_1635930242168.json")

@pytest.fixture()
def i_season_graph(load_json_file_as_graph):
    """Returns graph of an example NISV season in JSON-LD."""
    return load_json_file_as_graph(__file__, "rdf_season_1635930556031.json")

@pytest.fixture()
def i_series_graph(load_json_file_as_graph):
    """Returns graph of an example NISV series in JSON-LD."""
    return load_json_file_as_graph(__file__, "rdf_series_1635930663729.json")
