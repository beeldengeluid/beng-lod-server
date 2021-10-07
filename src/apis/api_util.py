MIME_TYPE_JSON_LD = 'application/ld+json'
MIME_TYPE_RDF_XML = 'application/rdf+xml'
MIME_TYPE_TURTLE = 'text/turtle'
MIME_TYPE_N_TRIPLES = 'application/n-triples'
MIME_TYPE_N3 = 'text/n3'
MIME_TYPE_JSON = 'application/json'

ACCEPT_TYPES = [
    MIME_TYPE_JSON_LD,
    MIME_TYPE_RDF_XML,
    MIME_TYPE_TURTLE,
    MIME_TYPE_N_TRIPLES,
    MIME_TYPE_JSON,
    MIME_TYPE_N3
]

MIME_TYPE_TO_LD = {
    MIME_TYPE_RDF_XML: 'xml',
    MIME_TYPE_JSON_LD: 'json-ld',
    MIME_TYPE_N_TRIPLES: 'nt',
    MIME_TYPE_TURTLE: 'ttl',
    MIME_TYPE_JSON: 'json-ld',
    MIME_TYPE_N3: 'n3'
}

def ld_to_mimetype():
    return {v: k for k, v in MIME_TYPE_TO_LD.items()}

def mimetype_to_ld(mime_type):
    return MIME_TYPE_TO_LD.get(mime_type, None)

def get_profile_by_uri(profile_uri, app_config):
    for p in app_config['PROFILES']:
        if p['uri'] == profile_uri:
            return p
    else:  # otherwise return the default profile
        return app_config['ACTIVE_PROFILE']

def extract_desired_formats(accept_type):
        mimetype = 'application/rdf+xml'
        if accept_type.find('rdf+xml') != -1:
            mimetype = 'application/rdf+xml'
        elif accept_type.find('json+ld') != -1:
            mimetype = 'application/ld+json'
        elif accept_type.find('json') != -1:
            mimetype = 'application/ld+json'
        elif accept_type.find('turtle') != -1:
            mimetype = 'text/turtle'
        elif accept_type.find('json') != -1:
            mimetype = 'text/n3'
        return mimetype, self.MIME_TYPE_TO_LD[mimetype]

def parse_accept_header(accept_header):
    """ Parses an Accept header for a request for RDF to the server. It returns the mime_type and profile.
    :param: accept_header: the Accept parameter from the HTTP request.
    :returns: mime_type, accept_profile. None if input parameter is missing.
    """
    mime_type = MIME_TYPE_JSON_LD
    accept_profile = None

    if accept_header is None or accept_header == '*/*':
        return mime_type, accept_profile

    if accept_header in ACCEPT_TYPES:
        return accept_header, accept_profile

    if accept_header.find(';') != -1 and accept_header.find('profile') != -1:
        temp = accept_header.split(';')
        if len(temp) == 2:
            mime_type = temp[0]

            kv = temp[1].split('=')
            if len(kv) > 1 and kv[0] == 'profile':
                accept_profile = kv[1].replace('"', '')
    return mime_type, accept_profile