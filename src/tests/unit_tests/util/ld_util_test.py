import pytest
from rdflib.namespace import SDO, RDF, SKOS
import requests
import json
from json.decoder import JSONDecodeError
from requests.exceptions import ConnectionError
from mockito import when, unstub, mock, verify, KWARGS
from models.DAANRdfModel import ResourceURILevel
from util.ld_util import generate_lod_resource_uri, get_lod_resource_from_rdf_store, \
    json_header_from_rdf_graph, json_iri_iri_from_rdf_graph, json_iri_lit_from_rdf_graph, \
    json_iri_bnode_from_rdf_graph, is_public_resource

DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"  # see setting_example.py
DUMMY_RESOURCE_ID = "1234"
DUMMY_RESOURCE_URI = f"{DUMMY_BENG_DATA_DOMAIN}id/scene/{DUMMY_RESOURCE_ID}"  # must be used in scene_rdf_xml.xml!
DUMMY_SPARQL_ENDPOINT = "http://sparql.beng.nl/sparql"
DUMMY_URI_NISV_ORGANISATION = "https://www.beeldengeluid.nl/"  # see setting_example.py


# noinspection PyTypeChecker
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
def test_get_lod_resource_from_rdf_store(scene_rdf_xml, resource_url, sparql_endpoint, nisv_organisation_uri,
                                         raise_connection_error, success):
    try:
        if raise_connection_error:
            when(requests).get(sparql_endpoint, **KWARGS).thenRaise(ConnectionError)
        else:
            resp = mock({"status_code": 200, "text": scene_rdf_xml})
            when(requests).get(sparql_endpoint, **KWARGS).thenReturn(resp)
        lod_graph = get_lod_resource_from_rdf_store(resource_url, sparql_endpoint, nisv_organisation_uri)

        # returns a Graph object when successful, otherwise returns None
        if success:
            assert lod_graph is not None
        else:
            assert lod_graph is None

        # requests.get is only called when there is a resource_url and sparql_endpoint
        if resource_url and sparql_endpoint:
            # ...but beware for the connection error, then only one request is fired
            if raise_connection_error is True:
                verify(requests, times=1).get(sparql_endpoint, **KWARGS)
            else:
                # ...otherwise three get requests will happen.
                verify(requests, times=3).get(sparql_endpoint, **KWARGS)
        else:
            verify(requests, times=0).get(sparql_endpoint, **KWARGS)
    finally:
        unstub()


def test_json_header_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_header_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 1
        # assert "o" in ui_data[0]
        assert all(x in ui_data[0] for x in ["o", "title"])
        assert all(x in ui_data[0]["o"] for x in ["uri", "prefix", "namespace", "property"])

        # only schema.org types (SDO) types are returned
        assert ui_data[0]["o"]["uri"] == f"{str(SDO)}Clip"
        assert ui_data[0]["o"]["namespace"] == str(SDO)
        assert ui_data[0]["o"]["property"] == "Clip"

    finally:
        unstub()


def test_json_iri_iri_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_iri_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 2
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            # there should be no RDF:type resources
            assert not (item["p"]["namespace"] == str(RDF) and item["p"]["property"] == "type")
            # all objects should be IRIs
            assert item["o"]["uri"].find("http") != -1
            assert all(x in ui_data[0]["p"] for x in ["uri", "prefix", "namespace", "property"])
            assert all(
                x in ui_data[0]["o"] for x in ["uri", "literal_form", "prefix", "namespace", "property", "pref_label"])

    finally:
        unstub()


def test_json_iri_lit_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_lit_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 1
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            assert all(x in item["p"] for x in ["uri", "prefix", "namespace", "property"])
            assert all(x in item["o"] for x in
                       ["literal_value", "datatype", "datatype_prefix", "datatype_namespace", "datatype_property"])

            # there should be no RDF:type resources
            assert not (item["p"]["namespace"] == str(RDF) and item["p"]["property"] == "type")
            assert item["o"]["literal_value"].find("http") == -1  # all objects should be Literals
    finally:
        unstub()


def test_json_iri_bnode_from_rdf_graph(program_rdf_graph_with_bnodes):
    try:
        ui_data = json_iri_bnode_from_rdf_graph(program_rdf_graph_with_bnodes, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 31
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            assert all(x in item["p"] for x in ["uri", "prefix", "namespace", "property"])

            for bnode_content in item["o"]:
                print(bnode_content)
                assert all(x in bnode_content for x in ["pred", "obj"])
                assert all(x in bnode_content["pred"] for x in ["uri", "prefix", "namespace", "property"])
                assert isinstance(bnode_content["obj"], str) or isinstance(bnode_content["obj"], dict)
                if isinstance(bnode_content["obj"], dict):
                    assert all(x in bnode_content["obj"] for x in
                               ["uri", "prefix", "namespace", "property", "pref_label"])

    finally:
        unstub()


@pytest.mark.parametrize(
    "resource_url, sparql_endpoint, ask_output, exception, expected_output",
    [
        (
                DUMMY_RESOURCE_URI,
                DUMMY_SPARQL_ENDPOINT,
                json.dumps({"head": {}, "boolean": True}),
                None,
                True
        ),
        (
                None,  # leave out the resource_url
                DUMMY_SPARQL_ENDPOINT,
                json.dumps({"head": {}, "boolean": True}),
                None,
                False
        ),
        (
                DUMMY_RESOURCE_URI,
                None,  # leave out the sparql_endpoint
                json.dumps({"head": {}, "boolean": True}),
                None,
                False
        ),
        (
                DUMMY_RESOURCE_URI,
                DUMMY_SPARQL_ENDPOINT,
                json.dumps({"head": {}, "boolean": False}),
                None,
                False
        ),
        (
                DUMMY_RESOURCE_URI,
                DUMMY_SPARQL_ENDPOINT,
                json.dumps({"head": {}, "boolean": False}),
                JSONDecodeError,  # forcefully raise JSONDecodeError
                False
        ),
        (
                DUMMY_RESOURCE_URI,
                DUMMY_SPARQL_ENDPOINT,
                json.dumps({"head": {}, "boolean": False}),
                ConnectionError,  # forcefully raise ConnectionError
                False
        ),
        (
                DUMMY_RESOURCE_URI,
                DUMMY_SPARQL_ENDPOINT,
                "{ CORRUPT JSON ]",  # corrupt the JSON to trigger exception
                None,  # a JSONDecodeError will be raised
                False
        )
    ],
)
def test_is_public_resource(resource_url, sparql_endpoint, ask_output, exception, expected_output):
    try:
        query = "ASK {<%s> ?p ?o . }" % resource_url
        if exception == ConnectionError:  # raise exception
            when(requests).get(
                DUMMY_SPARQL_ENDPOINT,
                params={"query": query, "format": "json"}
            ).thenRaise(exception)
        else:  # just return the ask_output
            when(requests).get(
                DUMMY_SPARQL_ENDPOINT,
                params={"query": query, "format": "json"}
            ).thenReturn(mock({"text": ask_output, "status_code": 200}))

        if exception == JSONDecodeError:  # raise JSONDecodeError on json.loads
            when(json).loads(ask_output).thenRaise(JSONDecodeError("error", ask_output, 0))

        assert is_public_resource(resource_url, sparql_endpoint) is expected_output

        # requests.get is only invoked with a valid resource_url and sparql_endpoint
        verify(requests, times=1 if resource_url and sparql_endpoint else 0).get(
            DUMMY_SPARQL_ENDPOINT,
            params={"query": query, "format": "json"}
        )
    finally:
        unstub()