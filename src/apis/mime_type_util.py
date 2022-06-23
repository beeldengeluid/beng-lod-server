from enum import Enum
from typing import Optional


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
