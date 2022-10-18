from apis.dataset.dataset_api import LODDataCatalogAPI


def test_init():
    lod_data_catalog_api = LODDataCatalogAPI()
    assert isinstance(lod_data_catalog_api, LODDataCatalogAPI)
