from apis.gtaa.gtaa_api import GTAAAPI
import pytest
from mockito import when, unstub, mock
from apis.mime_type_util import MimeType
import json
from rdflib import Graph
import requests

DUMMY_GTAA_IDENTIFIER = 123456
# DUMMY_MIMETYPE = "text/txet"
DUMMY_SPARQL_ENDPOINT = "http://enhupasakee.nu/sparql"
DUMMY_NAMED_GRAPH = "http://watmoetjedaarnu.mee/thes"
DUMMY_ORGANISATION = "http://www.doordeplee.nl/"
# DUMMY_PROFILE = "https://heelcomplexallemaal.nl/"
DUMMY_GTAA_URI = "http://data.beeldengeluid.nl/gtaa/123456"


def test_init():
    gtaa_api = GTAAAPI()
    assert isinstance(gtaa_api, GTAAAPI)


# @pytest.mark.parametrize(
#     "gtaa_uri, mime_type",
#     [
#         (DUMMY_GTAA_IDENTIFIER, MimeType.JSON_LD),
#         # (DUMMY_GTAA_IDENTIFIER, MimeType.RDF_XML),
#         # (DUMMY_GTAA_IDENTIFIER, MimeType.TURTLE),
#         # (DUMMY_GTAA_IDENTIFIER, MimeType.N_TRIPLES),
#         # (DUMMY_GTAA_IDENTIFIER, MimeType.N3),
#         # (DUMMY_GTAA_IDENTIFIER, MimeType.JSON),
#         # (DUMMY_GTAA_IDENTIFIER, "application/phony_mime_type"),
#     ],
# )
# def test_get_gtaa_lod_resource(i_get_gtaa_concept, gtaa_uri, mime_type):
#     # when the LOD resource is dereferenced, check the data
#     try:
#         api = GTAAAPI()
#         resp = mock({"status_code": 200, "text": i_get_gtaa_concept})
#         when(api).get(gtaa_uri).thenReturn(resp)

#         # when(requests).get(sparql_endpoint, **KWARGS).thenReturn(resp)

#         # when(ld_util).get_lod_resource_from_rdf_store(  DUMMY_GTAA_URI,
#         #                                                 DUMMY_SPARQL_ENDPOINT,
#         #                                                 DUMMY_ORGANISATION,
#         #                                                 DUMMY_NAMED_GRAPH).thenReturn(i_get_gtaa_concept)
#         resp = api.get(gtaa_uri)
#         assert resp.status_code == 200
#         assert type(resp) == str

#         g = Graph()
#         g.parse(resp, format=mime_type)        
#     # except PluginException:
#     #     assert mime_type == "application/phony_mime_type"
#     finally:
#         unstub()

#
# def test_get_gtaa_lod_view(i_get_gtaa_concept):
#     # when a HTML view is requested, test the lod
#     try:
#         api = GTAAAPI()
#         """    def _get_lod_view_gtaa(self, resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str,
#                            thesaurus_named_graph: str):"""
#         when(api)._get_lod_view_gtaa(DUMMY_GTAA_IDENTIFIER, DUMMY_SPARQL_ENDPOINT, DUMMY_ORGANISATION,
#                                 DUMMY_NAMED_GRAPH).thenReturn(i_get_gtaa_concept)
#
#         # api.get(DUMMY_GTAA_IDENTIFIER)
#     finally:
#         unstub()
