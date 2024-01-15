import pytest


@pytest.fixture()
def o_get_schema(open_file):
    """Returns an example version of the schema."""
    return open_file(__file__, "output_get_schema.ttl")

@pytest.fixture()
def i_ob_scene_rdf(load_json_file):
    """Returns RDF of an example Open Beelden item in JSON-LD."""
    return load_json_file(__file__, "rdf_ob_scene_2101703040124290024.json")
