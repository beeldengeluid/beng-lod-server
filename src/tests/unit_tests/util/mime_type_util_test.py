import pytest
from mockito import unstub
from apis.mime_type_util import parse_quality_values, parse_accept_header, MimeType

ACCEPT_HEADER_ALL = "*/*"
ACCEPT_HEADER_BENG = 'application/ld+json,profile="https://schema.org/"'
ACCEPT_HEADER_NDE = (
    "application/n-quads,application/trig;"
    "q=0.95,application/ld+json;q=0.9,"
    "application/n-triples;q=0.8,text/turtle;q=0.6,application/rdf+xml;q=0.5,"
    "application/jso5,text/n3;q=0.35,application/xml;q=0.3,text/xml;q=0.3,"
    "image/svg+xml;q=0.3,text/html;q=0.2,application/xhtml+xml;q=0.18"
)
ACCEPT_HEADER_FUJI = (
    "text/html, application/xhtml+xml, application/xml;q=0.5, text/xml;q=0.5, application/rdf+xml;q=0.5"
)
ACCEPT_HEADER_SPEC_1 = "text/plain; q=0.5, text/html,text/x-dvi; q=0.8, text/x-c"
ACCEPT_HEADER_SPEC_2 = "text/*, text/plain, text/plain;format=flowed, */*"
ACCEPT_HEADER_SPEC_3 = (
    "text/*;q=0.3, text/plain;q=0.7, text/plain;format=flowed, text/plain;format=fixed;q=0.4, */*;q=0.5"
)
ACCEPT_HEADER_CHROME = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
    "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
)
PROFILE_SDO = "https://schema.org/"


@pytest.mark.parametrize(
    "accept_header, mime_type, profile",
    [
        (ACCEPT_HEADER_ALL, MimeType.JSON_LD, None),
        (ACCEPT_HEADER_BENG, MimeType.JSON_LD, PROFILE_SDO),
        (ACCEPT_HEADER_NDE, MimeType.JSON_LD, None),
        (ACCEPT_HEADER_FUJI, MimeType.HTML, None),
        (ACCEPT_HEADER_CHROME, MimeType.HTML, None),
    ],
)
def test_parse_accept_header(accept_header, mime_type, profile):
    try:
        parse_result = parse_accept_header(accept_header)
        assert isinstance(parse_result[0], MimeType)
        if profile is not None:
            assert isinstance(parse_result[1], str)
        assert parse_result == (mime_type, profile)
    finally:
        unstub()


@pytest.mark.parametrize(
    "accept_header",
    [
        ACCEPT_HEADER_ALL,
        ACCEPT_HEADER_BENG,
        ACCEPT_HEADER_NDE,
        ACCEPT_HEADER_FUJI,
        ACCEPT_HEADER_CHROME,
    ],
)
def test_parse_quality_values(accept_header):
    """Parse the accept header for the NDE dataset register."""
    try:
        list_of_media_ranges = parse_quality_values(accept_header)
        assert isinstance(list_of_media_ranges, list)
        for mr in list_of_media_ranges:
            assert isinstance(mr, tuple)
            assert len(mr) == 2
    finally:
        unstub()
