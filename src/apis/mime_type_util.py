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


def get_profile_by_uri(profile_uri, app_config):
    for p in app_config["PROFILES"]:
        if p["uri"] == profile_uri:
            return p
    else:  # otherwise return the default profile
        return app_config["ACTIVE_PROFILE"]
