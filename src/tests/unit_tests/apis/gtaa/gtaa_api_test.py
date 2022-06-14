import pytest
import json
from lxml import etree
from mockito import when, unstub, verify, mock
from util.ld_util import get_lod_resource_from_rdf_store
from apis.mime_type_util import parse_accept_header, MimeType
from rdflib.plugin import PluginException
from apis.gtaa.gtaa_api import GTAAAPI
from rdflib import Graph

DUMMY_GTAA_IDENTIFIER = 123456
DUMMY_MIMETYPE = "text/txet"
DUMMY_SPARQL_ENDPOINT = "http://enhupasakee.nu/sparql"
DUMMY_NAMED_GRAPH = "http://watmoetjedaarnu.mee/thes"
DUMMY_ORGANISATION = "http://www.doordeplee.nl/"
DUMMY_PROFILE = "https://heelcomplexallemaal.nl/"
DUMMY_GTAA_URI = "http://data.beeldengeluid.nl/gtaa/123456"


# @pytest.mark.parametrize(
#     "gtaa_uri, mime_type",
#     [
#         (DUMMY_GTAA_IDENTIFIER, MimeType.JSON_LD),
#         (DUMMY_GTAA_IDENTIFIER, MimeType.RDF_XML),
#         (DUMMY_GTAA_IDENTIFIER, MimeType.TURTLE),
#         (DUMMY_GTAA_IDENTIFIER, MimeType.N_TRIPLES),
#         (DUMMY_GTAA_IDENTIFIER, MimeType.N3),
#         (DUMMY_GTAA_IDENTIFIER, MimeType.JSON),
#         (DUMMY_GTAA_IDENTIFIER, "application/phony_mime_type"),
#     ],
# )
# def test_get_gtaa_lod_resource(i_get_gtaa_concept, gtaa_uri, mime_type):
#     # when the LOD resource is dereferenced, check the data
#     try:
#         api = GTAAAPI()
#         """    def _get_lod_gtaa(self, gtaa_uri: str, mime_type: str, sparql_endpoint: str, nisv_organisation_uri: str,
#                       thesaurus_named_graph: str):"""
#         """def get_lod_resource_from_rdf_store(resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str,
#                                     named_graph: str = '') -> Optional[Graph]:"""
#         when(get_lod_resource_from_rdf_store(DUMMY_GTAA_URI,
#                                              DUMMY_SPARQL_ENDPOINT,
#                                              DUMMY_ORGANISATION,
#                                              DUMMY_NAMED_GRAPH)).thenReturn(i_get_gtaa_concept)
#         resp = api.get(DUMMY_GTAA_IDENTIFIER)
#         assert status_code == 200
#         if mime_type == MimeType.JSON_LD:
#             json_data = json.loads(resp)
#             assert type(resp) == str
#             assert type(json_data) == dict
#             # g = Graph()
#             # g.parse(resp, format="json-ld")
#         elif mime_type == MimeType.RDF_XML:
#             assert type(resp) == str
#             assert XML_ENCODING_DECLARATION in resp
#             root = etree.fromstring(resp.replace(XML_ENCODING_DECLARATION, ""))
#             assert type(root) == etree._Element
#         elif mime_type == MimeType.TURTLE:
#             assert type(resp) == str
#         elif mime_type == MimeType.N_TRIPLES:
#             assert type(resp) == str
#         elif mime_type == MimeType.N3:
#             assert type(resp) == str
#         elif mime_type == MimeType.JSON:
#             json_data = json.loads(resp)
#             assert type(resp) == str
#             assert type(json_data) == dict
#         # verify(dch, times=1).is_valid_dataset(DUMMY_DATASET_URI)
#     except PluginException:
#         assert mime_type == "application/phony_mime_type"
#     finally:
#         unstub()
#
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