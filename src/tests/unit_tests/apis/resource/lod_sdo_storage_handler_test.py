import pytest
import sys
from mockito import when, unstub
from apis.resource.SDOStorageLODHandler import SDOStorageLODHandler
from util.APIUtil import APIUtil
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF

""" ------------------------ fetchDocument -----------------------"""

DUMMY_SET = "dummy-set"
DUMMY_NOTATION = "dummy-notation"
SDO_PROFILE = 'https://schema.org/'
DUMMY_URL = "http://watmoetjedaarnu.mee"
RETURN_FORMAT_JSONLD = 'json-ld'


# def test_get_payload_scene_ob(application_settings, i_ob_scene_payload):
#     try:
#         sdo_handler = SDOStorageLODHandler(profile=SDO_PROFILE, config=application_settings)
#         when(SDOStorageLODHandler)._prepare_uri(DUMMY_SET, DUMMY_NOTATION).thenReturn(DUMMY_URL)
#         when(SDOStorageLODHandler._get_json_from_storage(DUMMY_URL)).thenReturn(i_ob_scene_payload)
#         data, status_code, headers = sdo_handler.get_storage_record(DUMMY_SET, DUMMY_NOTATION, RETURN_FORMAT_JSONLD)
#         assert status_code == 200
#
#         # load the resulting RDF data into a Graph
#         g = Graph()
#         g.load(data)
#
#         # test for existence of some triples
#         type_triple = (URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
#                        RDF.type,
#                        URIRef("https://schema.org/Clip"))
#         assert type_triple in g
#
#         license_triple = (URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
#                           URIRef("https://schema.org/license"),
#                           URIRef("http://rightsstatements.org/vocab/CNE/1.0/"))
#         assert license_triple in g
#
#         ob_uri_triple = (URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
#                          URIRef("https://schema.org/mainEntityOfPage"),
#                          URIRef("https://www.openbeelden.nl/media/1253547"))
#         assert ob_uri_triple in g
#
#     finally:
#         unstub()

    # when(SDOStorageLODHandler)._storage_2_lod(DUMMY_URL, RETURN_FORMAT_JSONLD).thenReturn(i_ob_scene_rdf)
