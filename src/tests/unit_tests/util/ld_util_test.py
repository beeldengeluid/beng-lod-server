import pytest

# note:
# the following SDO import generates a warning, see
# https://github.com/RDFLib/rdflib/issues/1830

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import SDO, RDF
from rdflib.compare import to_isomorphic
import requests
import json
from json.decoder import JSONDecodeError
from requests.exceptions import ConnectionError
from mockito import when, unstub, mock, verify, KWARGS
from models.DAANRdfModel import ResourceURILevel
from util.ld_util import (
    generate_lod_resource_uri,
    get_lod_resource_from_rdf_store,
    json_header_from_rdf_graph,
    json_iri_iri_from_rdf_graph,
    json_iri_lit_from_rdf_graph,
    json_iri_bnode_from_rdf_graph,
    is_public_resource,
    sparql_construct_query,
)

DUMMY_BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"  # see setting_example.py
DUMMY_RESOURCE_ID = "1234"
DUMMY_RESOURCE_URI = f"{DUMMY_BENG_DATA_DOMAIN}id/scene/{DUMMY_RESOURCE_ID}"  # must be used in scene_rdf_xml.xml!
DUMMY_SPARQL_ENDPOINT = "http://sparql.beng.example.com/sparql"
DUMMY_URI_NISV_ORGANISATION = "https://www.beeldengeluid.nl/"  # see setting_example.py
DUMMY_CONSTRUCT_QUERY = (
    "CONSTRUCT { ?s ?p ?o } WHERE { "
    "VALUES ?s { <http://data.beeldengeluid.nl/id/program/2101712160234752431> }"
    "?s ?p ?o FILTER(!ISBLANK(?o)) }"
)


@pytest.mark.parametrize(
    "resource_level, resource_id, beng_data_domain, resource_uri",
    [
        *[
            (
                level,  # program, series, season, scene, dataset, datacatalog, datadownload
                DUMMY_RESOURCE_ID,
                DUMMY_BENG_DATA_DOMAIN,
                f"{DUMMY_BENG_DATA_DOMAIN}id/{level.value}/{DUMMY_RESOURCE_ID}",
            )
            for level in ResourceURILevel
        ],
        (
            ResourceURILevel.PROGRAM,
            DUMMY_RESOURCE_ID,
            "BROKEN_BENG_DATA_DOMAIN",
            None,
        ),  # invalid beng_data_domain
        (
            "dataset",
            DUMMY_RESOURCE_ID,
            DUMMY_RESOURCE_ID,
            None,
        ),  # invalid level param (no str allowed)
        (
            "program",
            DUMMY_RESOURCE_ID,
            DUMMY_RESOURCE_ID,
            None,
        ),  # another invalid level param
    ],
)
def test_generate_lod_resource_uri(
    resource_level, resource_id, beng_data_domain, resource_uri
):
    try:
        assert (
            generate_lod_resource_uri(resource_level, resource_id, beng_data_domain)
            == resource_uri
        )
    finally:
        unstub()


@pytest.mark.parametrize(
    "resource_url, sparql_endpoint, nisv_organisation_uri",
    [
        (
            DUMMY_RESOURCE_URI,
            DUMMY_SPARQL_ENDPOINT,
            DUMMY_URI_NISV_ORGANISATION,
        ),
    ],
)
def test_get_lod_resource_from_rdf_store_success(
    scene_rdf_xml,
    resource_url,
    sparql_endpoint,
    nisv_organisation_uri,
):
    try:
        resp = mock({"status_code": 200, "text": scene_rdf_xml})
        when(requests).get(sparql_endpoint, **KWARGS).thenReturn(resp)
        lod_graph = get_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, nisv_organisation_uri
        )

        # returns a Graph object when successful, otherwise returns None
        assert isinstance(lod_graph, Graph)

        # requests.get is only called when there is a resource_url and sparql_endpoint
        if resource_url and sparql_endpoint:
            # sparql_construct is called 4 times for catalog object and 6 times for GTAA object
            verify(requests, atleast=4).get(sparql_endpoint, **KWARGS)
        else:
            verify(requests, times=0).get(sparql_endpoint, **KWARGS)
    finally:
        unstub()


@pytest.mark.parametrize(
    "resource_url, sparql_endpoint, nisv_organisation_uri",
    [
        (DUMMY_RESOURCE_URI, None, DUMMY_URI_NISV_ORGANISATION),
        (None, DUMMY_SPARQL_ENDPOINT, DUMMY_URI_NISV_ORGANISATION),
    ],
)
def test_get_lod_resource_from_rdf_store_none(
    scene_rdf_xml,
    resource_url,
    sparql_endpoint,
    nisv_organisation_uri,
):
    try:
        resp = mock({"status_code": 200, "text": scene_rdf_xml})
        when(requests).get(sparql_endpoint, **KWARGS).thenReturn(resp)
        lod_graph = get_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, nisv_organisation_uri
        )

        # returns a Graph object when successful, otherwise returns None
        assert lod_graph is None

        # requests.get is only called when there is a resource_url and sparql_endpoint
        if resource_url and sparql_endpoint:
            # sparql_construct is called 4 times for catalog object and 6 times for GTAA object
            verify(requests, atleast=4).get(sparql_endpoint, **KWARGS)
        else:
            verify(requests, times=0).get(sparql_endpoint, **KWARGS)
    finally:
        unstub()


@pytest.mark.parametrize(
    "resource_url,sparql_endpoint,nisv_organisation_uri",
    [
        (
            DUMMY_RESOURCE_URI,
            DUMMY_SPARQL_ENDPOINT,
            DUMMY_URI_NISV_ORGANISATION,
        ),
    ],
)
def test_get_lod_get_lod_resource_from_rdf_store_connection_error(
    resource_url,
    sparql_endpoint,
    nisv_organisation_uri,
):
    try:
        when(requests).get(sparql_endpoint, **KWARGS).thenRaise(ConnectionError)
        lod_graph = get_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, nisv_organisation_uri
        )
        assert lod_graph is None

        # requests.get is only called when there is a resource_url and sparql_endpoint
        if resource_url and sparql_endpoint:
            verify(requests, atleast=1).get(sparql_endpoint, **KWARGS)
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
        assert all(
            x in ui_data[0]["o"] for x in ["uri", "prefix", "namespace", "property"]
        )

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
            assert not (
                item["p"]["namespace"] == str(RDF) and item["p"]["property"] == "type"
            )
            # all objects should be IRIs
            assert item["o"]["uri"].find("http") != -1
            assert all(
                x in ui_data[0]["p"] for x in ["uri", "prefix", "namespace", "property"]
            )
            assert all(
                x in ui_data[0]["o"]
                for x in [
                    "uri",
                    "literal_form",
                    "prefix",
                    "namespace",
                    "property",
                    "pref_label",
                ]
            )

    finally:
        unstub()


def test_json_iri_lit_from_rdf_graph(scene_rdf_graph):
    try:
        ui_data = json_iri_lit_from_rdf_graph(scene_rdf_graph, DUMMY_RESOURCE_URI)
        assert type(ui_data) == list
        assert len(ui_data) == 1
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            assert all(
                x in item["p"] for x in ["uri", "prefix", "namespace", "property"]
            )
            assert all(
                x in item["o"]
                for x in [
                    "literal_value",
                    "datatype",
                    "datatype_prefix",
                    "datatype_namespace",
                    "datatype_property",
                ]
            )

            # there should be no RDF:type resources
            assert not (
                item["p"]["namespace"] == str(RDF) and item["p"]["property"] == "type"
            )
            assert (
                item["o"]["literal_value"].find("http") == -1
            )  # all objects should be Literals
    finally:
        unstub()


def test_json_iri_bnode_from_rdf_graph(program_rdf_graph_with_bnodes):
    try:
        ui_data = json_iri_bnode_from_rdf_graph(
            program_rdf_graph_with_bnodes, DUMMY_RESOURCE_URI
        )
        assert type(ui_data) == list
        assert len(ui_data) == 31
        for item in ui_data:
            assert all(x in item for x in ["o", "p"])
            assert all(
                x in item["p"] for x in ["uri", "prefix", "namespace", "property"]
            )

            for bnode_content in item["o"]:
                print(bnode_content)
                assert all(x in bnode_content for x in ["pred", "obj"])
                assert all(
                    x in bnode_content["pred"]
                    for x in ["uri", "prefix", "namespace", "property"]
                )
                assert isinstance(bnode_content["obj"], str) or isinstance(
                    bnode_content["obj"], dict
                )
                if isinstance(bnode_content["obj"], dict):
                    if isinstance(bnode_content, URIRef):
                        assert all(
                            x in bnode_content["obj"]
                            for x in [
                                "uri",
                                "prefix",
                                "namespace",
                                "property",
                                "pref_label",
                            ]
                        )
                    if isinstance(bnode_content, Literal):
                        assert all(x in bnode_content["obj"] for x in ["label"])

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
            True,
        ),
        (
            None,  # leave out the resource_url
            DUMMY_SPARQL_ENDPOINT,
            json.dumps({"head": {}, "boolean": True}),
            None,
            False,
        ),
        (
            DUMMY_RESOURCE_URI,
            None,  # leave out the sparql_endpoint
            json.dumps({"head": {}, "boolean": True}),
            None,
            False,
        ),
        (
            DUMMY_RESOURCE_URI,
            DUMMY_SPARQL_ENDPOINT,
            json.dumps({"head": {}, "boolean": False}),
            None,
            False,
        ),
        (
            DUMMY_RESOURCE_URI,
            DUMMY_SPARQL_ENDPOINT,
            json.dumps({"head": {}, "boolean": False}),
            JSONDecodeError,  # forcefully raise JSONDecodeError
            False,
        ),
        (
            DUMMY_RESOURCE_URI,
            DUMMY_SPARQL_ENDPOINT,
            json.dumps({"head": {}, "boolean": False}),
            ConnectionError,  # forcefully raise ConnectionError
            False,
        ),
        (
            DUMMY_RESOURCE_URI,
            DUMMY_SPARQL_ENDPOINT,
            "{ CORRUPT JSON ]",  # corrupt the JSON to trigger exception
            None,  # a JSONDecodeError will be raised
            False,
        ),
    ],
)
def test_is_public_resource(
    resource_url, sparql_endpoint, ask_output, exception, expected_output
):
    try:
        query = "ASK {<%s> ?p ?o . }" % resource_url
        if exception == ConnectionError:  # raise exception
            when(requests).get(
                DUMMY_SPARQL_ENDPOINT, params={"query": query, "format": "json"}
            ).thenRaise(exception)
        else:  # just return the ask_output
            when(requests).get(
                DUMMY_SPARQL_ENDPOINT, params={"query": query, "format": "json"}
            ).thenReturn(mock({"text": ask_output, "status_code": 200}))

        if exception == JSONDecodeError:  # raise JSONDecodeError on json.loads
            when(json).loads(ask_output).thenRaise(
                JSONDecodeError("error", ask_output, 0)
            )

        assert is_public_resource(resource_url, sparql_endpoint) is expected_output

        # requests.get is only invoked with a valid resource_url and sparql_endpoint
        verify(requests, times=1 if resource_url and sparql_endpoint else 0).get(
            DUMMY_SPARQL_ENDPOINT, params={"query": query, "format": "json"}
        )
    finally:
        unstub()


@pytest.mark.parametrize(
    "sparql_endpoint, query", [(DUMMY_SPARQL_ENDPOINT, DUMMY_CONSTRUCT_QUERY)]
)
def test_sparql_construct_query(program_rdf_xml, sparql_endpoint, query):
    try:
        resp = mock({"status_code": 200, "text": program_rdf_xml})
        when(resp).raise_for_status().thenReturn(None)
        when(requests).get(sparql_endpoint, **KWARGS).thenReturn(resp)
        g1 = sparql_construct_query(sparql_endpoint, query)
        g2 = Graph()
        g2.parse(data=resp.text, format="xml")
        assert to_isomorphic(g1) == to_isomorphic(g2)
    finally:
        unstub()
