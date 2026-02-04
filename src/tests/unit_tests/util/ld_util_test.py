import pytest
import requests
from enum import Enum
from rdflib import Graph
from rdflib.compare import to_isomorphic
from requests.exceptions import ConnectionError
from typing import List, Tuple, Union

from mockito import when, unstub, mock, verify, KWARGS
from models.DatasetApiUriLevel import DatasetApiUriLevel
from models.ResourceApiUriLevel import ResourceApiUriLevel
from util.ld_util import (
    generate_lod_resource_uri,
    get_lod_resource_from_rdf_store,
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

generate_lod_resource_uri_cases: List[
    Tuple[Union[Enum, str], str, str, Union[str, None]]
] = []
generate_lod_resource_uri_cases += [
    (
        level,  # program, series, season, scene
        DUMMY_RESOURCE_ID,
        DUMMY_BENG_DATA_DOMAIN,
        f"{DUMMY_BENG_DATA_DOMAIN}id/{level.value}/{DUMMY_RESOURCE_ID}",
    )
    for level in ResourceApiUriLevel
]
generate_lod_resource_uri_cases += [
    (
        level,  # datacatalog, dataset, datadownload
        DUMMY_RESOURCE_ID,
        DUMMY_BENG_DATA_DOMAIN,
        f"{DUMMY_BENG_DATA_DOMAIN}id/{level.value}/{DUMMY_RESOURCE_ID}",
    )
    for level in DatasetApiUriLevel
]

generate_lod_resource_uri_cases += [
    (
        ResourceApiUriLevel.PROGRAM,
        DUMMY_RESOURCE_ID,
        "BROKEN_BENG_DATA_DOMAIN",
        "",
    ),  # invalid beng_data_domain
    (
        "dataset",
        DUMMY_RESOURCE_ID,
        DUMMY_RESOURCE_ID,
        "",
    ),  # invalid level param (no str allowed)
    (
        "program",
        DUMMY_RESOURCE_ID,
        DUMMY_RESOURCE_ID,
        "",
    ),  # another invalid level param
]


@pytest.mark.parametrize(
    "resource_level, resource_id, beng_data_domain, resource_uri",
    generate_lod_resource_uri_cases,
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
        g2.parse(data=program_rdf_xml, format="xml")
        assert to_isomorphic(g1) == to_isomorphic(g2)
    finally:
        unstub()
