import pytest


"""------------------------ DATA CATALOG HANDLER ----------------------"""


@pytest.fixture(scope="module")
def i_datacatalog(load_file_as_graph):
    return load_file_as_graph(__file__, "example_data_catalog.ttl")


@pytest.fixture(scope="module")
def i_dataset(load_file_as_graph):
    return load_file_as_graph(__file__, "example_dataset.ttl")


@pytest.fixture(scope="module")
def i_datadownload(load_file_as_graph):
    return load_file_as_graph(__file__, "example_datadownload.ttl")
