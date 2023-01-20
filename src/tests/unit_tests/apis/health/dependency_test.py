from http import HTTPStatus

from mockito import mock, when
import pytest
import requests
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    InvalidSchema,
    Timeout,
    TooManyRedirects,
    URLRequired,
)

import apis.health.DependencyHealth
from apis.health.DependencyHealth import Dependency, DependencyHealth


TEST_CONFIG_KEY = "EXAMPLE_HEALTH_ENDPOINT"
TEST_HEALTH_URL = "https://example.com/health"
TEST_HEALTH_TIMEOUT_SEC = 5.0


@pytest.fixture(scope="function")
def dependency():
    yield Dependency(TEST_CONFIG_KEY, TEST_HEALTH_URL)


def test_init():
    dependency = Dependency(TEST_CONFIG_KEY, TEST_HEALTH_URL)
    assert dependency.config_key == TEST_CONFIG_KEY
    assert dependency.health_url == TEST_HEALTH_URL
    assert isinstance(dependency, Dependency)


@pytest.mark.parametrize(
    "requests_response, expected_dependency_health",
    [
        (
            mock(
                {"body": "", "status_code": http_status.value},
                spec=requests.Response,
            ),
            DependencyHealth(http_status),
        )
        for http_status in HTTPStatus
    ],
)
def test_get_health_on_response(
    dependency: Dependency,
    requests_response: requests.Response,
    expected_dependency_health: DependencyHealth,
):
    with (
        when(apis.health.DependencyHealth.requests)
        .get(dependency.health_url, timeout=TEST_HEALTH_TIMEOUT_SEC)
        .thenReturn(requests_response)
    ):
        health = dependency.get_health(TEST_HEALTH_TIMEOUT_SEC)
        assert health == expected_dependency_health


@pytest.mark.parametrize(
    "exception",
    [
        ConnectionError,
        HTTPError,
        TooManyRedirects,
        Timeout,
    ],
)
def test_get_health_on_external_errors(dependency, exception):
    with (
        when(apis.health.DependencyHealth.requests)
        .get(dependency.health_url, timeout=TEST_HEALTH_TIMEOUT_SEC)
        .thenRaise(exception)
    ):
        dependency_health = dependency.get_health(TEST_HEALTH_TIMEOUT_SEC)
        assert dependency_health == DependencyHealth(None)


@pytest.mark.parametrize(
    "exception",
    [
        # client-related exceptions
        InvalidSchema,
        URLRequired,
        # general exceptions
        OverflowError,
        Exception,
    ],
)
def test_get_health_on_internal_errors(dependency, exception):
    """we should still receive exceptions not due to external issues"""
    with (
        when(apis.health.DependencyHealth.requests)
        .get(dependency.health_url, timeout=TEST_HEALTH_TIMEOUT_SEC)
        .thenRaise(exception)
    ):
        with pytest.raises(exception):
            dependency.get_health(TEST_HEALTH_TIMEOUT_SEC)
