import pytest


@pytest.fixture(scope="module")
def gtaa_url():
    def genGtaaURL(type, identifier):
        return f"/gtaa/{identifier}"

    return genGtaaURL


@pytest.fixture()
def i_gtaa_graph(load_file_as_graph):
    """Returns graph of an example gtaa concept in JSON-LD."""
    return load_file_as_graph(__file__, "concept_36350.json")
