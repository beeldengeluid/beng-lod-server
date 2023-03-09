import pytest


@pytest.fixture()
def o_get_schema(open_file):
    """Returns an example version of the schema."""
    return open_file(__file__, "output_get_schema.ttl")


@pytest.fixture()
def i_ob_scene_payload(load_json_file):
    """Returns payload metadata for Open Beelden item from Flex data store in JSON format."""
    return load_json_file(__file__, "payload_ob_scene_2101703040124290024.json")


@pytest.fixture()
def i_ob_scene_rdf(load_json_file):
    """Returns RDF of an example Open Beelden item in JSON-LD."""
    return load_json_file(__file__, "rdf_ob_scene_2101703040124290024.json")


@pytest.fixture()
def i_error_scene_payload(load_json_file):
    """Returns payload metadata for Open Beelden item from Flex data store in JSON format."""
    return load_json_file(__file__, "error_payload_scene_2101702260627885424.json")


@pytest.fixture()
def i_program_payload_material_type(load_json_file):
    """Checks whether the payload contains the 'material type' information.
    Returns payload metadata for Open Beelden item from Flex data store in JSON format.
    """
    return load_json_file(__file__, "payload_program_2101608170156857531.json")
