from apis.dataset.dataset_api import LODDataAPI


def test_init():
    lod_data_api = LODDataAPI()
    assert isinstance(lod_data_api, LODDataAPI)
