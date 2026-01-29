from apis.link.link_api import LinkAPI


def test_init():
    link_api = LinkAPI()
    assert isinstance(link_api, LinkAPI)
