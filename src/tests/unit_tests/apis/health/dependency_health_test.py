from http import HTTPStatus

from mockito import mock, unstub, verifyStubbedInvocationsAreUsed, when
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


@pytest.mark.parametrize(
    "status_code, expected_is_ok",
    [
        # we expect ok for an ok http status
        (HTTPStatus.OK, True),
        # we don't expect ok for all http statuses other than OK
        *[
            (http_status.value, False)
            for http_status in HTTPStatus
            if http_status != HTTPStatus.OK
        ],
        # we don't expect ok for a missing status (e.g. due to connection error)
        (None, False),
    ],
)
def test_dependency_health_is_ok(status_code: HTTPStatus, expected_is_ok: bool):
    try:
        dependency_health = DependencyHealth(status_code)
        assert dependency_health.is_ok() == expected_is_ok
    finally:
        unstub()


TEST_CONFIG_KEY = "EXAMPLE_HEALTH_ENDPOINT"
TEST_HEALTH_URL = "https://example.com/health"


@pytest.mark.parametrize(
    "config_key, health_url, requests_response, requests_exception, expected_dependency_health, expected_exception",
    [
        # if requests returns a response, its status_code should be returned
        *[
            (
                TEST_CONFIG_KEY,
                TEST_HEALTH_URL,
                mock(
                    {"body": "", "status_code": http_status.value},
                    spec=requests.Response,
                ),
                None,
                DependencyHealth(http_status.value),
                None,
            )
            for http_status in HTTPStatus
        ],
        # if requests throws server-related exceptions, None should be returned
        (
            TEST_CONFIG_KEY,
            TEST_HEALTH_URL,
            None,
            ConnectionError,
            DependencyHealth(None),
            None,
        ),
        (
            TEST_CONFIG_KEY,
            TEST_HEALTH_URL,
            None,
            HTTPError,
            DependencyHealth(None),
            None,
        ),
        (
            TEST_CONFIG_KEY,
            TEST_HEALTH_URL,
            None,
            TooManyRedirects,
            DependencyHealth(None),
            None,
        ),
        (TEST_CONFIG_KEY, TEST_HEALTH_URL, None, Timeout, DependencyHealth(None), None),
        # if requests throws client-related exceptions, they should be raised
        (TEST_CONFIG_KEY, TEST_HEALTH_URL, None, InvalidSchema, None, InvalidSchema),
        (TEST_CONFIG_KEY, TEST_HEALTH_URL, None, URLRequired, None, URLRequired),
        # general exceptions should be raised as well
        (TEST_CONFIG_KEY, TEST_HEALTH_URL, None, OverflowError, None, OverflowError),
        (TEST_CONFIG_KEY, TEST_HEALTH_URL, None, Exception, None, Exception),
    ],
)
def test_dependency(
    config_key: str,
    health_url: str,
    requests_response: requests.Response,
    requests_exception: Exception,
    expected_dependency_health: DependencyHealth,
    expected_exception: Exception,
):
    try:
        dependency = Dependency(config_key, health_url)
        health_timeout_sec = 5.0

        # test __init__ and accessors
        assert dependency.config_key == TEST_CONFIG_KEY
        assert dependency.health_url == TEST_HEALTH_URL

        # test get_dependency_health
        if requests_exception:
            when(apis.health.DependencyHealth.requests).get(
                TEST_HEALTH_URL, timeout=health_timeout_sec
            ).thenRaise(requests_exception)
        else:
            when(apis.health.DependencyHealth.requests).get(
                TEST_HEALTH_URL, timeout=health_timeout_sec
            ).thenReturn(requests_response)
        if expected_dependency_health:
            health = dependency.get_health(health_timeout_sec)
            assert health == expected_dependency_health
        elif expected_exception:
            try:
                dependency.get_health(health_timeout_sec)
            except expected_exception:
                # we got the expected_exception
                pass
            except Exception:
                # we got an unexcpected exception
                raise AssertionError()
        else:
            # this shouldn't happen, get_health() should return or raise
            raise AssertionError()

    finally:
        verifyStubbedInvocationsAreUsed()
        unstub()
