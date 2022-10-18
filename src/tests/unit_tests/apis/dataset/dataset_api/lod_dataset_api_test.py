from apis.dataset.dataset_api import LODDatasetAPI

# TODO: test the lod_view for datasets


def test_init():
    lod_dataset_api = LODDatasetAPI()
    assert isinstance(lod_dataset_api, LODDatasetAPI)
