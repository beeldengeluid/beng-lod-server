import pytest


@pytest.fixture(scope="module")
def datacatalog_url():
    def genDatacatalogURL(identifier):
        return f"/id/datacatalog/{identifier}"

    return genDatacatalogURL


@pytest.fixture(scope="module")
def datadownload_url():
    def genDatadownloadURL(identifier):
        return f"/id/datadownload/{identifier}"

    return genDatadownloadURL


@pytest.fixture(scope="module")
def dataset_url():
    def genDatasetURL(identifier):
        return f"/id/dataset/{identifier}"

    return genDatasetURL


@pytest.fixture(scope="module")
def i_datacatalog(load_file_as_graph):
    """Returns graph of an example data catalog"""
    return load_file_as_graph(__file__, "data_catalog_unit_test.ttl")


@pytest.fixture(scope="module")
def i_dataset(load_file_as_graph):
    """Returns graph of an example dataset"""
    return load_file_as_graph(__file__, "dataset.json")


@pytest.fixture(scope="module")
def i_datadownload(load_file_as_graph):
    """Returns graph of an example datadownload"""
    return load_file_as_graph(__file__, "datadownload.json")
