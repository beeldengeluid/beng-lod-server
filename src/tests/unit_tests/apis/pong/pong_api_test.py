from mockito import unstub

from apis.pong.pong_api import Pong


def test_get_pong():
    try:
        pong = Pong()
        assert pong.get() == "pong"
    finally:
        unstub()
