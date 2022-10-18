from apis.resource.resource_api import ResourceAPI


def test_init():
    resource_api = ResourceAPI()
    assert isinstance(resource_api, ResourceAPI)
