import logging
import re
from enum import Enum
from typing import Optional, List, Tuple


class MimeType(Enum):
    JSON_LD = "application/ld+json"
    RDF_XML = "application/rdf+xml"
    TURTLE = "text/turtle"
    N_TRIPLES = "application/n-triples"
    N3 = "text/n3"
    JSON = "application/json"
    HTML = "text/html"

    def to_ld_format(self) -> Optional[str]:
        if self is MimeType.JSON_LD:
            return "json-ld"
        elif self is MimeType.RDF_XML:
            return "xml"
        elif self is MimeType.TURTLE:
            return "ttl"
        elif self is MimeType.N_TRIPLES:
            return "nt11"
        elif self is MimeType.N3:
            return "n3"
        elif self is MimeType.JSON:
            return "json-ld"
        elif self is MimeType.HTML:
            return None


def accept_type_to_mime_type(accept_type: str) -> MimeType:
    mt = MimeType.RDF_XML
    if accept_type.find("rdf+xml") != -1:
        mt = MimeType.RDF_XML
    elif accept_type.find("json+ld") != -1:
        mt = MimeType.JSON_LD
    elif accept_type.find("ld+json") != -1:
        mt = MimeType.JSON_LD
    elif accept_type.find("json-ld") != -1:
        mt = MimeType.JSON_LD
    elif accept_type.find("json") != -1:
        mt = MimeType.JSON_LD
    elif accept_type.find("turtle") != -1:
        mt = MimeType.TURTLE
    elif accept_type.find("n3") != -1:
        mt = MimeType.N3
    elif accept_type.find("nt11") != -1:
        mt = MimeType.N_TRIPLES
    return mt


def ld_to_mimetype_map():
    ld_to_mt = {}
    for mt in MimeType:
        ld_to_mt[mt.to_ld_format()] = mt
    return ld_to_mt


def get_profile_by_uri(profile_uri, app_config):
    for p in app_config["PROFILES"]:
        if p["uri"] == profile_uri:
            return p
    else:  # otherwise return the default profile
        return app_config["ACTIVE_PROFILE"]


def parse_quality_values(accept_header_text: str) -> List[Tuple]:
    """This parses the Accept header and returns a list of media_type/quality_factor tuples.
          Accept = #( media-range [ weight ] )

            media-range    = ( "*/*"
                             / ( type "/" "*" )
                             / ( type "/" subtype )
                           ) parameters

        examples:
            Accept: text/*, text/plain, text/plain;format=flowed, */*
            Accept: text/*;q=0.3, text/plain;q=0.7, text/plain;format=flowed,
                    text/plain;format=fixed;q=0.4, */*;q=0.5

         weight = OWS ";" OWS "q=" qvalue
          qvalue = ( "0" [ "." 0*3DIGIT ] )
                    / ( "1" [ "." 0*3("0") ] )
    """
    media_range_parts = re.split(r",\s*", accept_header_text)
    list_of_mr = [re.split(r";\s*q=", media_range) for media_range in media_range_parts]
    l_accept = [
        (item[0], float(item[1])) if len(item) == 2 else (item[0], 1)
        for item in list_of_mr
    ]

    # TODO: handle the media range parameters, like  text/plain;format=flowed,
    # TODO: order based on specificity (more specific has higher priority

    l_accept.sort(key=lambda a: a[1], reverse=True)  # order based on quality

    return l_accept


def parse_accept_header(accept_header: str) -> (MimeType, str):
    """Parses an Accept header for a request for RDF to the server. It returns the mime_type and profile.

    Profile negotiation (kind of a hack):
    By definition (https://www.rfc-editor.org/rfc/rfc9110.html#name-accept), the accept header is a comma separated
    list of media ranges. We assume that the profile is always the last part of the accept header, being the part
    after the last comma that always starts with 'profile='. Because of this assumption we can split the entire
    string at the commas and handle the profile as an exceptional case.

    :param: accept_header: the Accept parameter from the HTTP request.
    :returns: mime_type, accept_profile. None if input parameter is missing.
    """
    mime_type = MimeType.JSON_LD
    accept_profile = None

    if accept_header is None or accept_header == "*/*":
        return mime_type, accept_profile

    # handle the profile (example: profile="https://schema.org/")
    profile_param = re.split(r",profile=", accept_header, maxsplit=1)
    if len(profile_param) == 2:
        accept_profile = profile_param[1].strip('"')

    # now continue without the profile part (when present).
    accept_header = profile_param[0]

    # parse the relative quality factor https://github.com/beeldengeluid/beng-lod-server/issues/215
    media_ranges = parse_quality_values(accept_header)
    for media_range in media_ranges:
        try:
            mime_type = MimeType(media_range[0])
            return mime_type, accept_profile
        except ValueError as e:
            print(str(e))

    try:
        return MimeType(accept_header), accept_profile
    except ValueError as e:
        logging.error(f"Accept header not a valid mimetype: {str(e)}")
        return MimeType.JSON_LD, accept_profile
