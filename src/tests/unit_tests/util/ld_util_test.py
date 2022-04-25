import pytest
from rdflib.namespace import SDO, RDF
import requests
from requests.exceptions import ConnectionError
from mockito import when, unstub, mock, verify, KWARGS
from models.DAANRdfModel import ResourceURILevel
from util.ld_util import generate_lod_resource_uri, get_lod_resource_from_rdf_store, \
    json_header_from_rdf_graph, json_iri_iri_from_rdf_graph, json_iri_lit_from_rdf_graph, \
    json_iri_bnode_from_rdf_graph

DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"  # see setting_example.py
DUMMY_RESOURCE_ID = "1234"
DUMMY_RESOURCE_URI = f"{DUMMY_BENG_DATA_DOMAIN}id/scene/{DUMMY_RESOURCE_ID}"  # must be used in scene_rdf_xml.xml!
DUMMY_SPARQL_ENDPOINT = "http://sparql.beng.nl/sparql"
DUMMY_URI_NISV_ORGANISATION = "https://www.beeldengeluid.nl/"  # see setting_example.py

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


@pytest.mark.parametrize(
    "resource_url, sparql_endpoint, nisv_organisation_uri, raise_connection_error, success",
    [
        (DUMMY_RESOURCE_URI, DUMMY_SPARQL_ENDPOINT, DUMMY_URI_NISV_ORGANISATION, False, True),
        (DUMMY_RESOURCE_URI, DUMMY_SPARQL_ENDPOINT, DUMMY_URI_NISV_ORGANISATION, True, False),
        (DUMMY_RESOURCE_URI, None, DUMMY_URI_NISV_ORGANISATION, False, False),
        (None, DUMMY_SPARQL_ENDPOINT, DUMMY_URI_NISV_ORGANISATION, False, False),
    ],
)
def test_get_lod_resource_from_rdf_store(scene_rdf_xml, resource_url, sparql_endpoint, nisv_organisation_uri, raise_connection_error, success):
    try:
        if raise_connection_error:
            when(requests).get(sparql_endpoint, **KWARGS).thenRaise(ConnectionError)
        else:
            resp = mock({"status_code" : 200, "text" : scene_rdf_xml})
            when(requests).get(sparql_endpoint, **KWARGS).thenReturn(resp)
        lod_graph = get_lod_resource_from_rdf_store(resource_url, sparql_endpoint, nisv_organisation_uri)
        
        # returns a Graph object when successful, otherwise returns None
        if success:
            assert lod_graph is not None 
        else:
            assert lod_graph is None
            
        # requests.get is only called when there is a resource_url and sparql_endpoint
        if resource_url and sparql_endpoint:
            verify(requests, times=1).get(sparql_endpoint, **KWARGS)
        else:
            verify(requests, times=0).get(sparql_endpoint, **KWARGS)
    finally:
        unstub()


def test_json_header_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_header_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 1
        assert "o" in ui_data[0]
        assert ui_data[0]["o"] == f"{str(SDO)}Clip"  # only schema.org types are returned
    finally:
        unstub()


def test_json_iri_iri_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_iri_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 2
        for item in ui_data:
            assert all(x in item for x in ["o", "p", "property", "namespace"])
            assert item["p"].find(str(RDF)) == -1  # there should be no RDF:type resources
            assert item["o"].find("http") != -1  # all objects should be IRIs
    finally:
        unstub()


def test_json_iri_lit_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_lit_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 1
        for item in ui_data:
            assert all(x in item for x in ["o", "p", "property", "namespace", "type_o"])
            assert item["p"].find(str(RDF)) == -1  # there should be no RDF:type resources
            assert item["o"].find("http") == -1  # all objects should be Literals
    finally:
        unstub()


# TODO need another RDF/XML example that has blank node content to test better!
def test_json_iri_bnode_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_bnode_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 1
        for item in ui_data:
            assert all(x in item for x in ["o", "p", "property", "namespace"])
            assert item["o"] == []  # TODO in this example there is just an empty blank node...
    finally:
        unstub()


def test_is_public_resource():
    try:
        pass
    finally:
        unstub()
