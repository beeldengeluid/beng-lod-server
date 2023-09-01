import pytest
import requests
from requests.exceptions import ConnectionError
import json
from mockito import when, unstub, mock, verify
from apis.resource.StorageLODHandler import StorageLODHandler

DUMMY_STORAGE_BASE_URL = "http://flexstore:1234"
DUMMY_ID = 12345  # ID's are passed as an int (see the resource_api)
DUMMY_STORAGE_URL = f"{DUMMY_STORAGE_BASE_URL}/storage/series/{DUMMY_ID}"
DUMMY_STORAGE_DATA = {
    "id": "2101703040124290024",
    "parents": [{"parent_type": "ITEM", "parent_id": "2101608310097797221"}],
    "payload": {"nisv.programid": {"value": "PGM4011489"}},
    "aclGroups": [
        {
            "name": "NISV_ADMINISTRATOR",
            "read": "1",
            "write": "1",
            "nameRead": "NISV_ADMINISTRATOR_1",
        }
    ],
    "site_id": "LTI98960475_POS106992639",
    "date_created": 1488660755348,
    "date_last_updated": 1488660755437,
    "media_start": 907.0,
    "media_duration": 82.0,
    "media_group": [],
    "payload_model": "http://flexstore.beng.example.com/model/api/metadata/form/nisv-lti-sel-film-sound/r1",
    "viz_type": "LOGTRACKITEM",
    "logtrack_type": "scenedesc",
    "program_ref_id": "2101608140120072331",
    "internal_ref_id": "2101608310113256223",
    "acl_hash": 581299796,
}


@pytest.fixture(scope="function")
def storage_lod_handler(application_settings):
    yield StorageLODHandler(application_settings)


def test_init(storage_lod_handler):
    assert isinstance(storage_lod_handler, StorageLODHandler)


@pytest.mark.parametrize(
    "storage_base_url, level, identifier, storage_uri",
    [
        (
            DUMMY_STORAGE_BASE_URL,
            "series",
            DUMMY_ID,
            f"{DUMMY_STORAGE_BASE_URL}/storage/series/{DUMMY_ID}",
        ),
        (
            DUMMY_STORAGE_BASE_URL,
            "season",
            DUMMY_ID,
            f"{DUMMY_STORAGE_BASE_URL}/storage/season/{DUMMY_ID}",
        ),
        (
            DUMMY_STORAGE_BASE_URL,
            "program",
            DUMMY_ID,
            f"{DUMMY_STORAGE_BASE_URL}/storage/program/{DUMMY_ID}",
        ),
        (
            DUMMY_STORAGE_BASE_URL,
            "scene",
            DUMMY_ID,
            f"{DUMMY_STORAGE_BASE_URL}/storage/logtrackitem/{DUMMY_ID}",
        ),
        ("BROKEN_STORAGE_BASE_URL", "scene", DUMMY_ID, None),
    ],
)
def test_prepare_storage_uri(
    storage_lod_handler, storage_base_url, level, identifier, storage_uri
):
    try:
        assert (
            storage_lod_handler._prepare_storage_uri(
                storage_base_url, level, identifier
            )
            == storage_uri
        )
    finally:
        unstub()


@pytest.mark.parametrize(
    "status_code, response_text, exception, expected_output",
    [
        (200, json.dumps(DUMMY_STORAGE_DATA), None, DUMMY_STORAGE_DATA),  # happy flow
        # any non-200 will be raised
        # (500, None, None, None),
        # (400, None, None, None),
        # (403, None, None, None),
        # (404, None, None, None),
        (200, "BROKEN JSON", None, None),  # broken JSON data will result in None
        (
            200,
            None,
            ConnectionError,
            None,
        ),  # these exceptions are caught and result in None
        (200, None, json.decoder.JSONDecodeError("bla", "{}", 0), None),
    ],
)
def test_get_json_from_storage(
    storage_lod_handler, status_code, response_text, exception, expected_output
):
    try:
        response = mock({"status_code": status_code, "text": response_text})
        if exception is None:
            when(requests).get(DUMMY_STORAGE_URL).thenReturn(response)
        else:
            when(requests).get(DUMMY_STORAGE_URL).thenRaise(exception)
        assert (
            storage_lod_handler._get_json_from_storage(DUMMY_STORAGE_URL)
            == expected_output
        )
        verify(requests, times=1).get(DUMMY_STORAGE_URL)
    finally:
        unstub()
