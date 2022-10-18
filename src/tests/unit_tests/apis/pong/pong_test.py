import pytest
from apis.pong.pong_api import Pong


@pytest.fixture(scope="function")
def pong():
    yield Pong()


def test_init(pong):
    assert isinstance(pong, Pong)


def test_get(pong):
    assert pong.get() == "pong"
