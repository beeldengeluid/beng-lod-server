from enum import Enum
from typing import Optional


class MimeType(Enum):
    JSON_LD = 'application/ld+json'
    RDF_XML = 'application/rdf+xml'
    TURTLE = 'text/turtle'
    N_TRIPLES = 'application/n-triples'
    N3 = 'text/n3'
    JSON = 'application/json'

    def to_ld_format(self) -> Optional[str]:
        if self == MimeType.JSON_LD:
            return 'json-ld'
        elif self == MimeType.RDF_XML:
            return 'xml'
        elif self == MimeType.TURTLE:
            return 'ttl'
        elif self == MimeType.N_TRIPLES:
            return 'nt11'
        elif self == MimeType.N3:
            return 'n3'
        elif self == MimeType.JSON:
            return 'json-ld'
        return None


def accept_type_to_mime_type(accept_type: str) -> MimeType:
    mt = MimeType.RDF_XML
    if accept_type.find('rdf+xml') != -1:
        mt = MimeType.RDF_XML
    elif accept_type.find('json+ld') != -1:
        mt = MimeType.JSON_LD
    elif accept_type.find('json') != -1:
        mt = MimeType.JSON_LD
    elif accept_type.find('turtle') != -1:
        mt = MimeType.TURTLE
    elif accept_type.find('n3') != -1:
        mt = MimeType.N3
    elif accept_type.find('nt11') != -1:
        mt = MimeType.N_TRIPLES
    return mt


def ld_to_mimetype_map():
    ld_to_mt = {}
    for mt in MimeType:
        ld_to_mt[mt.to_ld_format()] = mt
    return ld_to_mt


def get_profile_by_uri(profile_uri, app_config):
    for p in app_config['PROFILES']:
        if p['uri'] == profile_uri:
            return p
    else:  # otherwise return the default profile
        return app_config['ACTIVE_PROFILE']


def parse_accept_header(accept_header: str) -> (MimeType, str):
    """ Parses an Accept header for a request for RDF to the server. It returns the mime_type and profile.
    :param: accept_header: the Accept parameter from the HTTP request.
    :returns: mime_type, accept_profile. None if input parameter is missing.
    """
    mime_type = MimeType.JSON_LD
    accept_profile = None

    if accept_header is None or accept_header == '*/*':
        return mime_type, accept_profile

    try:
        return MimeType(accept_header), accept_profile
    except ValueError as e:
        print(f'accept header not a valid mimetype {str(e)}')

    if accept_header.find(';') != -1 and accept_header.find('profile') != -1:
        temp = accept_header.split(';')
        if len(temp) == 2:
            try:
                mime_type = MimeType(temp[0])
            except ValueError as e:
                print(e)

            kv = temp[1].split('=')
            if len(kv) > 1 and kv[0] == 'profile':
                accept_profile = kv[1].replace('"', '')
    return mime_type, accept_profile
