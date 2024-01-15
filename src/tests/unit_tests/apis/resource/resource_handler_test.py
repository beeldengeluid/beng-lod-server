import pytest

from mockito import when, unstub, verify, ANY
from rdflib import Graph

import util.ld_util 

from apis.resource.ResourceHandler import ResourceHandler
from models.ResourceURILevel import ResourceURILevel
from util.mime_type_util import MimeType

@pytest.mark.parametrize('mime_type',[
MimeType.JSON_LD,
MimeType.HTML
])
def test_get_200(mime_type):
    DUMMY_IDENTIFIER = "dummy-identifier"
    DUMMY_URL = f"https://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "just something pretending to be an HTML page"
    DUMMY_GRAPH = Graph()
    DUMMY_DOMAIN = "dummy domain"
    DUMMY_ENDPOINT = "https://dummy"
    DUMMY_NISV_ORGANISATION = "nisv"
    DUMMY_SERIALISED_GRAPH = "just something pretending to be a serialisation of a graph"
    CAT_TYPE = "program"
    resource_handler = ResourceHandler

    try:
        when(util.ld_util).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, DUMMY_DOMAIN).thenReturn(DUMMY_URL)
        if mime_type is MimeType.HTML:
            when(resource_handler)._get_lod_view_resource(DUMMY_URL, DUMMY_ENDPOINT, DUMMY_NISV_ORGANISATION).thenReturn(DUMMY_PAGE)
        else:
            when(util.ld_util).get_lod_resource_from_rdf_store(DUMMY_URL, DUMMY_ENDPOINT, DUMMY_NISV_ORGANISATION).thenReturn(DUMMY_GRAPH)
            when(DUMMY_GRAPH).serialize(format=mime_type).thenReturn(DUMMY_SERIALISED_GRAPH)

        resource_handler.get_lod_for_resource_in_type(mime_type, DUMMY_IDENTIFIER, DUMMY_DOMAIN, DUMMY_ENDPOINT, DUMMY_NISV_ORGANISATION, CAT_TYPE)

        verify(util.ld_util, times=1).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, DUMMY_DOMAIN)
        if mime_type is MimeType.HTML:
            verify(resource_handler, times=1)._get_lod_view_resource(DUMMY_URL, DUMMY_ENDPOINT, DUMMY_NISV_ORGANISATION)
        else:
            verify(util.ld_util, times=1).get_lod_resource_from_rdf_store(DUMMY_URL, DUMMY_ENDPOINT, DUMMY_NISV_ORGANISATION)
            verify(DUMMY_GRAPH, times=1).serialize(format=mime_type)
    finally:
        unstub()

@pytest.mark.parametrize("cause", [
    "no_mime_type",
    "generate_uri_failed"
])
def test_get_400(cause):
    DUMMY_IDENTIFIER = "dummy-identifier"
    DUMMY_DOMAIN = "dummy domain"
    DUMMY_ENDPOINT = "https://dummy"
    DUMMY_NISV_ORGANISATION = "nisv"
    CAT_TYPE = "program"
    resource_handler = ResourceHandler

    if cause == "no_mime_type":
        BAD_MIME_TYPE = None
        msg, code, explaination = resource_handler.get_lod_for_resource_in_type(BAD_MIME_TYPE, DUMMY_IDENTIFIER, DUMMY_DOMAIN, DUMMY_ENDPOINT, DUMMY_NISV_ORGANISATION, CAT_TYPE)
        assert code == 400

    elif cause == "generate_uri_failed":
        DUMMY_MIME_TYPE = "dummy mime type"
        with when(util.ld_util).generate_lod_resource_uri(ResourceURILevel(CAT_TYPE), DUMMY_IDENTIFIER, DUMMY_DOMAIN).thenRaise(ValueError):
            msg, code, explaination = resource_handler.get_lod_for_resource_in_type(DUMMY_MIME_TYPE, DUMMY_IDENTIFIER, DUMMY_DOMAIN, DUMMY_ENDPOINT, DUMMY_NISV_ORGANISATION, CAT_TYPE)
            assert code == 400
    else:
        raise ValueError("Bad test variable")

