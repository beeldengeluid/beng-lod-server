from apis.health.health_api import Health


def test_init():
    health_api = Health()
    assert isinstance(health_api, Health)
