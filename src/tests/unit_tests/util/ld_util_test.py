import pytest
from mockito import when, unstub, mock, verify
from models.DAANRdfModel import ResourceURILevel
from util.ld_util import generate_lod_resource_uri

DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"
DUMMY_RESOURCE_ID = "1234"


@pytest.mark.parametrize(
    "resource_level, resource_id, beng_data_domain, resource_uri",
    [
        (
            level,  # program, series, season, scene, dataset, datacatalog, datadownload
            DUMMY_RESOURCE_ID, 
            DUMMY_BENG_DATA_DOMAIN, 
            f"{DUMMY_BENG_DATA_DOMAIN}id/{level.value}/{DUMMY_RESOURCE_ID}"
        ) for level in ResourceURILevel
    ] + [
        (ResourceURILevel.PROGRAM, DUMMY_RESOURCE_ID, "BROKEN_BENG_DATA_DOMAIN", None),  # invalid beng_data_domain
        ("dataset", DUMMY_RESOURCE_ID, DUMMY_RESOURCE_ID, None),  # invalid level param (no str allowed)
        ("program", DUMMY_RESOURCE_ID, DUMMY_RESOURCE_ID, None)  # another invalid level param
    ],
)
def test_generate_lod_resource_uri(resource_level, resource_id, beng_data_domain, resource_uri):
    try:
        assert generate_lod_resource_uri(resource_level, resource_id, beng_data_domain) == resource_uri
    finally:
        unstub()


def test_get_lod_resource_from_rdf_store():
    try:
        pass
    finally:
        unstub()

def test_json_header_from_rdf_graph():
    try:
        pass
    finally:
        unstub()

def test_json_iri_iri_from_rdf_graph():
    try:
        pass
    finally:
        unstub()

def test_json_iri_lit_from_rdf_graph():
    try:
        pass
    finally:
        unstub()

def test_json_iri_bnode_from_rdf_graph():
    try:
        pass
    finally:
        unstub()

def test_is_public_resource():
    try:
        pass
    finally:
        unstub()
