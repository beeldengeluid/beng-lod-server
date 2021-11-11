from mockito import when, unstub
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from apis.mime_type_util import MimeType
from cache import cache
from flask import Flask


""" ------------------------ fetchDocument -----------------------"""

DUMMY_SET = "dummy-set"
DUMMY_NOTATION = "dummy-notation"
SDO_PROFILE = 'https://schema.org/'
DUMMY_URL = "http://watmoetjedaarnu.mee"
RETURN_FORMAT_JSONLD = 'application/ld+json'


def test_get_payload_scene_ob(application_settings, i_ob_scene_payload):
    try:
        # # setup the test client
        # app = Flask(__name__)

        # init cache
        cache.init_app(application_settings)

        profile = application_settings.get('ACTIVE_PROFILE')
        sdo_handler = profile['storage_handler'](application_settings, profile)
        when(sdo_handler)._prepare_storage_uri(DUMMY_SET, DUMMY_NOTATION).thenReturn(DUMMY_URL)
        when(sdo_handler)._get_json_from_storage(DUMMY_URL).thenReturn(i_ob_scene_payload)
        mt = MimeType(RETURN_FORMAT_JSONLD)
        resp, status_code, headers = sdo_handler.get_storage_record(
            DUMMY_SET,
            DUMMY_NOTATION,
            mt.to_ld_format()
        )
        assert status_code == 200

        # load the resulting RDF data into a Graph
        g = Graph()
        g.parse(data=resp, format=mt.to_ld_format())

        # test for number of triples
        assert len(g) == 30

        # test for existence of some triples
        type_triple = (URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
                       RDF.type,
                       URIRef("https://schema.org/Clip"))
        assert type_triple in g

        license_triple = (URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
                          URIRef("https://schema.org/license"),
                          URIRef("http://rightsstatements.org/vocab/CNE/1.0/"))
        assert license_triple in g

        ob_uri_triple = (URIRef("http://data.beeldengeluid.nl/id/scene/2101703040124290024"),
                         URIRef("https://schema.org/mainEntityOfPage"),
                         URIRef("https://www.openbeelden.nl/media/1253547"))
        assert ob_uri_triple in g

    finally:
        unstub()
