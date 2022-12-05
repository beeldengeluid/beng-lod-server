import pytest
from copy import deepcopy
from mockito import when, unstub
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SDO
from rdflib.plugin import PluginException
from models.SDORdfConcept import SDORdfConcept
from apis.mime_type_util import MimeType
from apis.resource.SDOStorageLODHandler import SDOStorageLODHandler


DUMMY_LEVEL = "program"
SDO_PROFILE = "https://schema.org/"
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
    "payload_model": "http://flexstore.beng.nl/model/api/metadata/form/nisv-lti-sel-film-sound/r1",
    "viz_type": "LOGTRACKITEM",
    "logtrack_type": "scenedesc",
    "program_ref_id": "2101608140120072331",
    "internal_ref_id": "2101608310113256223",
    "acl_hash": 581299796,
}

DUMMY_STORAGE_DATA__UNSUPPORTED_LOGTRACK_TYPE = deepcopy(DUMMY_STORAGE_DATA)
DUMMY_STORAGE_DATA__UNSUPPORTED_LOGTRACK_TYPE[
    "logtrack_type"
] = "unsupported logtrack type"


def test_get_storage_record__ob_scene_payload(application_settings, i_ob_scene_payload):
    try:
        profile = application_settings.get("ACTIVE_PROFILE")
        storage_base_url = application_settings.get("STORAGE_BASE_URL")
        sdo_handler = profile["storage_handler"](application_settings, profile)
        when(sdo_handler)._prepare_storage_uri(
            storage_base_url, DUMMY_LEVEL, DUMMY_ID
        ).thenReturn(DUMMY_STORAGE_URL)
        when(sdo_handler)._get_json_from_storage(DUMMY_STORAGE_URL).thenReturn(
            i_ob_scene_payload
        )
        mt = MimeType.JSON_LD
        resp, status_code, headers = sdo_handler.get_storage_record(
            DUMMY_LEVEL, DUMMY_ID, mt.to_ld_format()
        )
        assert status_code == 200

        # load the resulting RDF data into a Graph
        g = Graph()
        g.parse(data=resp, format=mt.to_ld_format())

        # test for number of triples
        assert len(g) == 31

        # test for existence of some triples
        type_triple = (
            URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
            RDF.type,
            SDO.Clip,
        )
        assert type_triple in g

        license_triple = (
            URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
            SDO.license,
            URIRef("http://rightsstatements.org/vocab/CNE/1.0/"),
        )
        print(license_triple)
        print(g)
        assert license_triple in g

        ob_uri_triple = (
            URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
            SDO.mainEntityOfPage,
            URIRef("https://www.openbeelden.nl/media/1253547"),
        )
        assert ob_uri_triple in g

    finally:
        unstub()


def test_get_storage_record__error_scene_payload(
    application_settings, i_error_scene_payload
):
    try:
        profile = application_settings.get("ACTIVE_PROFILE")
        storage_base_url = application_settings.get("STORAGE_BASE_URL")
        sdo_handler = profile["storage_handler"](application_settings, profile)
        when(sdo_handler)._prepare_storage_uri(
            storage_base_url, "scene", "2101702260627885424"
        ).thenReturn(DUMMY_STORAGE_URL)
        when(sdo_handler)._get_json_from_storage(DUMMY_STORAGE_URL).thenReturn(
            i_error_scene_payload
        )
        mt = MimeType.JSON_LD
        resp, status_code, headers = sdo_handler.get_storage_record(
            "scene", "2101702260627885424", mt.to_ld_format()
        )
        assert status_code == 200

    except UnicodeEncodeError as e:
        print(str(e))
    finally:
        unstub()


def test_get_storage_record__no_storage_data(application_settings):
    """Tests for a proper handling of errors with the flex store."""
    try:
        profile = application_settings.get("ACTIVE_PROFILE")
        storage_base_url = application_settings.get("STORAGE_BASE_URL")
        sdo_handler = profile["storage_handler"](application_settings, profile)
        when(sdo_handler)._prepare_storage_uri(
            storage_base_url, "scene", "2101702260627885424"
        ).thenReturn(DUMMY_STORAGE_URL)
        when(sdo_handler)._get_json_from_storage(DUMMY_STORAGE_URL).thenReturn(None)
        mt = MimeType.JSON_LD
        resp, status_code, headers = sdo_handler.get_storage_record(
            "scene", "2101702260627885424", mt.to_ld_format()
        )
        assert status_code == 500

    except AssertionError as err:
        print(str(err))
    finally:
        unstub()


"""
---------------------------------- PER FUNCTION UNIT TESTS --------------------------------
"""


@pytest.fixture(scope="function")
def sdo_storage_lod_handler(application_settings):
    active_profile = application_settings.get("ACTIVE_PROFILE")
    yield SDOStorageLODHandler(application_settings, active_profile)


def test_init(sdo_storage_lod_handler):
    assert isinstance(sdo_storage_lod_handler, SDOStorageLODHandler)


# TODO
def test_get_storage_record(sdo_storage_lod_handler):
    pass


@pytest.mark.parametrize(
    "storage_url, return_mime_type",
    [
        (DUMMY_STORAGE_URL, MimeType.JSON_LD),
        (DUMMY_STORAGE_URL, MimeType.RDF_XML),
        (DUMMY_STORAGE_URL, MimeType.TURTLE),
        (DUMMY_STORAGE_URL, MimeType.N_TRIPLES),
        (DUMMY_STORAGE_URL, MimeType.N3),
        (DUMMY_STORAGE_URL, MimeType.JSON),  # not supported by rdflib
    ],
)
def test_storage_2_lod(sdo_storage_lod_handler, storage_url, return_mime_type):
    try:
        when(sdo_storage_lod_handler)._get_json_from_storage(storage_url).thenReturn(
            DUMMY_STORAGE_DATA
        )
        serialized_data = sdo_storage_lod_handler._storage_2_lod(
            storage_url, return_mime_type.value
        )
        assert type(serialized_data) == str

        # test deserialisation (includes json, xml parsing)
        Graph().parse(data=serialized_data, format=return_mime_type.value)
    except PluginException:  # MimeType.JSON is not supported by rdflib
        assert return_mime_type == MimeType.JSON
    finally:
        unstub()


@pytest.mark.parametrize(
    "storage_data, raised_exception",
    [
        (DUMMY_STORAGE_DATA, None),
        (DUMMY_STORAGE_DATA__UNSUPPORTED_LOGTRACK_TYPE, ValueError),
    ],
)
def test_transform_json_to_rdf(sdo_storage_lod_handler, storage_data, raised_exception):
    try:
        concept = sdo_storage_lod_handler._transform_json_to_rdf(storage_data)
        if raised_exception is None:
            assert type(concept) == SDORdfConcept
    except ValueError:
        assert raised_exception == ValueError
    finally:
        unstub()
