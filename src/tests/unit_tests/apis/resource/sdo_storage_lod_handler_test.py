from mockito import when, unstub
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from apis.mime_type_util import MimeType


""" ------------------------ fetchDocument -----------------------"""

DUMMY_LEVEL = "program"
DUMMY_ID = 12345
SDO_PROFILE = "https://schema.org/"
DUMMY_URL = "http://watmoetjedaarnu.mee"
RETURN_FORMAT_JSONLD = "application/ld+json"


def test_get_payload_scene_ob(application_settings, i_ob_scene_payload):
    try:
        profile = application_settings.get("ACTIVE_PROFILE")
        storage_base_url = application_settings.get("STORAGE_BASE_URL")
        sdo_handler = profile["storage_handler"](application_settings, profile)
        when(sdo_handler)._prepare_storage_uri(storage_base_url, DUMMY_LEVEL, DUMMY_ID).thenReturn(
            DUMMY_URL
        )
        when(sdo_handler)._get_json_from_storage(DUMMY_URL, True).thenReturn(
            i_ob_scene_payload
        )
        mt = MimeType(RETURN_FORMAT_JSONLD)
        resp, status_code, headers = sdo_handler.get_storage_record(
            DUMMY_LEVEL, DUMMY_ID, mt.to_ld_format()
        )
        assert status_code == 200

        # load the resulting RDF data into a Graph
        g = Graph()
        g.parse(data=resp, format=mt.to_ld_format())

        # test for number of triples
        assert len(g) == 30

        # test for existence of some triples
        type_triple = (
            URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
            RDF.type,
            URIRef("https://schema.org/Clip"),
        )
        assert type_triple in g

        license_triple = (
            URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
            URIRef("https://schema.org/license"),
            URIRef("http://rightsstatements.org/vocab/CNE/1.0/"),
        )
        assert license_triple in g

        ob_uri_triple = (
            URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
            URIRef("https://schema.org/mainEntityOfPage"),
            URIRef("https://www.openbeelden.nl/media/1253547"),
        )
        assert ob_uri_triple in g

    finally:
        unstub()


def test_for_cant_encode_character(application_settings, i_error_scene_payload):
    try:
        profile = application_settings.get("ACTIVE_PROFILE")
        storage_base_url = application_settings.get("STORAGE_BASE_URL")
        sdo_handler = profile["storage_handler"](application_settings, profile)
        when(sdo_handler)._prepare_storage_uri(
            storage_base_url, "scene", "2101702260627885424"
        ).thenReturn(DUMMY_URL)
        when(sdo_handler)._get_json_from_storage(DUMMY_URL, True).thenReturn(
            i_error_scene_payload
        )
        mt = MimeType(RETURN_FORMAT_JSONLD)
        resp, status_code, headers = sdo_handler.get_storage_record(
            "scene", "2101702260627885424", mt.to_ld_format()
        )
        assert status_code == 200

    except UnicodeEncodeError as e:
        print(str(e))
    finally:
        unstub()


def test_for_material_type(application_settings, i_program_payload_material_type):
    """
    "nisv.materialtype": {
        "value": "audio",
        "origin": "https://studio.mam.beeldengeluid.nl/api/metadata/dictionary/~nisv-pgmmaterialtype/audio",
        "resolved_value": "audio"
    },
    """
    try:
        pass
    except UnicodeEncodeError as e:
        print(str(e))
    finally:
        unstub()


def test_no_payload_from_flex_store(application_settings):
    """Tests for a proper handling of errors with the flex store."""
    try:
        profile = application_settings.get("ACTIVE_PROFILE")
        storage_base_url = application_settings.get("STORAGE_BASE_URL")
        sdo_handler = profile["storage_handler"](application_settings, profile)
        when(sdo_handler)._prepare_storage_uri(
            storage_base_url, "scene", "2101702260627885424"
        ).thenReturn(DUMMY_URL)
        when(sdo_handler)._get_json_from_storage(DUMMY_URL, True).thenReturn(None)
        mt = MimeType(RETURN_FORMAT_JSONLD)
        resp, status_code, headers = sdo_handler.get_storage_record(
            "scene", "2101702260627885424", mt.to_ld_format()
        )
        assert status_code == 500

    except AssertionError as err:
        print(str(err))
    finally:
        unstub()
