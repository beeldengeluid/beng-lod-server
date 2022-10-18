from http import HTTPStatus

import pytest

from apis.health.DependencyHealth import DependencyHealth


@pytest.mark.parametrize("status_code", HTTPStatus)
def test_init(status_code):
    dependency_health = DependencyHealth(status_code)
    assert isinstance(dependency_health, DependencyHealth)


def test_is_ok_on_ok_status():
    """dependencies with an ok http status (200) are ok"""
    dependency_health = DependencyHealth(HTTPStatus.OK)
    assert dependency_health.is_ok() is True


@pytest.mark.parametrize(
    "status_code",
    [http_status.value for http_status in HTTPStatus if http_status != HTTPStatus.OK],
)
def test_is_ok_on_not_ok_status(status_code: HTTPStatus):
    """dependencies with an http status other than ok (200) are not ok"""
    dependency_health = DependencyHealth(status_code)
    assert dependency_health.is_ok() is False


def test_is_ok_on_missing_status():
    """dependencies with a missing http missing status (e.g. connection error) are not ok"""
    dependency_health = DependencyHealth(None)
    assert dependency_health.is_ok() is False
