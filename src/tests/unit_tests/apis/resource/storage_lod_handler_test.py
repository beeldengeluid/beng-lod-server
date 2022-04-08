import pytest
from mockito import when, unstub
from apis.resource.StorageLODHandler import StorageLODHandler
from models.DAANJsonModel import ObjectType

DUMMY_STORAGE_BASE_URL = "http://flexstore:1234"
DUMMY_ID = 12345  # ID's are passed as an int (see the resource_api)

@pytest.mark.parametrize(
    "storage_base_url, level, identifier, storage_uri",
    [
        (DUMMY_STORAGE_BASE_URL, "series", DUMMY_ID, f"{DUMMY_STORAGE_BASE_URL}/storage/series/{DUMMY_ID}"),
        (DUMMY_STORAGE_BASE_URL, "season", DUMMY_ID, f"{DUMMY_STORAGE_BASE_URL}/storage/season/{DUMMY_ID}"),
        (DUMMY_STORAGE_BASE_URL, "program", DUMMY_ID, f"{DUMMY_STORAGE_BASE_URL}/storage/program/{DUMMY_ID}"),
        (DUMMY_STORAGE_BASE_URL, "scene", DUMMY_ID, f"{DUMMY_STORAGE_BASE_URL}/storage/logtrackitem/{DUMMY_ID}"),
        ("BROKEN_STORAGE_BASE_URL", "scene", DUMMY_ID, None),
    ],
)
def test_prepare_storage_uri(application_settings, storage_base_url, level, identifier, storage_uri):
    try:
        slh = StorageLODHandler(application_settings)
        assert slh._prepare_storage_uri(storage_base_url, level, identifier) == storage_uri
    finally:
        unstub()
