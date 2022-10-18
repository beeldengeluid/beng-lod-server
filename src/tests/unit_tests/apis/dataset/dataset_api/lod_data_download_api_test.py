from apis.dataset.dataset_api import LODDataDownloadAPI


def test_init():
    lod_data_download_api = LODDataDownloadAPI()
    assert isinstance(lod_data_download_api, LODDataDownloadAPI)
