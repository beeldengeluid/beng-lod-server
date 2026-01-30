import logging
import requests
import validators
import json
from typing import Optional
from requests.exceptions import ConnectionError, HTTPError
from urllib.parse import urlparse, urlunparse
from rdflib import Graph, URIRef, BNode, Literal
from util.ns_util import (
    SCHEMA,
    SDO,
    WIKIDATA,
    WIKIDATA_WWW,
    SKOS,
    DCTERMS,
    DISCOGS_ARTIST,
    DISCOGS_RELEASE,
    MUZIEKWEB,
    MUZIEKWEB_VOCAB,
    MUZIEKSCHATTEN,
    RDFS,
    MUSICBRAINZ_RELEASE,
    QUDT,
)

logger = logging.getLogger()


def generate_muziekweb_lod_resource_uri(path: str, muziekweb_data_domain: str) -> str:
    """Constructs valid url using the data domain and the path.
    :param path: the Muziekweb path (both /Link and /vocab are supported)
    :param muziekweb_data_domain: see MUZIEKWEB_DATA_DOMAIN in config.yml
    :returns: a proper URI as it should be listed in the LOD server.
    """
    url_parts = urlparse(str(muziekweb_data_domain))
    if url_parts.netloc is not None and url_parts.netloc != "":
        parts = (url_parts.scheme, url_parts.netloc, path, "", "", "")
        return urlunparse(parts)
    else:
        return ""


def is_muziekweb_resource(resource_url: str, sparql_endpoint: str) -> bool:
    """Check with the triple store whether the resource exists."""
    query = f"ASK {{ {{ <{resource_url}> ?p ?o }} }}"
    params = {"query": query, "format": "application/json"}
    resp = requests.get(sparql_endpoint, params=params)
    resp.raise_for_status()
    if resp.status_code == 200:
        if resp.json().get("boolean"):
            return True
    return False


def get_resource_from_rdf_store(
    resource_url: str,
    sparql_endpoint: str,
    query_fname: str,
    organisation_uri: str,
) -> Graph:
    """Given a resource URI, the data is retrieved from the SPARQL endpoint.
    This is done as generic as possible by using the lodview pattern of getting
    all triples and triples for blank nodes associated with the resource, in one query.

    :param resource_url: the resource URI to be retrieved.
    :param sparql_endpoint: the SPARQL endpoint URL.
    :param query_fname: filename of the query to be used.
    :param organisation_uri: URI for the publishing organisation.
    :returns: the RDF data as a GRAPH (merged graph for core triples and bnode triples).
    """
    g = Graph(bind_namespaces="core")
    if not resource_url:
        return g
    if not sparql_endpoint or validators.url(sparql_endpoint) is False:
        return g

    try:
        query_str = get_query_from_file(query_fname)
        query = query_str.replace("?resource_iri", f"<{resource_url}>")
        logger.debug(f"SPARQL query to get the resource:\n{query}")

        # get the results
        query_result = sparql_select_query(sparql_endpoint, query, format="json")
        results = json.loads(query_result)
        logger.debug(f"SPARQL query results: {results}")

        # Note we have to add the resource_url for the triples that miss the subject 's'
        g += convert_results_to_graph(results, resource_url)

        if len(g) == 0:
            logger.error("Graph was empty")

        # add the missing namespaces
        g.bind("schema", SCHEMA)
        g.bind("sdo", SDO)
        g.bind("wd", WIKIDATA)
        g.bind("wikidata", WIKIDATA_WWW)
        g.bind("skos", SKOS)
        g.bind("dcterms", DCTERMS)
        g.bind("discogs-artist", DISCOGS_ARTIST)
        g.bind("discogs-release", DISCOGS_RELEASE)
        g.bind("muziekweb", MUZIEKWEB)
        g.bind("som", MUZIEKSCHATTEN)
        g.bind("vocab", MUZIEKWEB_VOCAB)
        g.bind("rdfs", RDFS)
        g.bind("mb-release", MUSICBRAINZ_RELEASE)
        g.bind("qudt", QUDT)

        logger.debug(f"TODO: do something with the organisation uri {organisation_uri}")

        return g
    except ConnectionError as e:
        logger.exception(e)
    except HTTPError as e:
        logger.exception(e)
    return g


def get_query_from_file(filepath: str) -> str:
    """Return the query read from the query file."""
    query_string = ""
    with open(filepath, encoding="utf-8") as qf:
        query_string = qf.read()
    return query_string


def sparql_select_query(
    sparql_endpoint: str,
    query: str,
    format: str = "xml",
    session: Optional[requests.Session] = None,
) -> str:
    """Sends a SPARQL SELECT query to the SPARQL endpoint and returns the result in a string in the specified format
    raises a ConnectionError when the sparql endpoint can not be reached, or
    raises an HTTPError when the request was not successful.
    :param sparql_endpoint - the endpoint to be queried
    :param query - the SELECT query
    :param format - the format to retrun the data in, default is 'xml'
    :param session - optional, a session to reuse when querying the endpoint"""
    result_string = ""

    if session:
        resp = session.get(
            url=sparql_endpoint,
            params={"query": query},
            headers={
                "Accept": f"{'application/sparql-results+json' if format == 'json' else 'application/sparql-results+xml'}"
            },
        )
    else:
        resp = requests.get(
            sparql_endpoint,
            params={"query": query},
            headers={
                "Accept": f"{'application/sparql-results+json' if format == 'json' else 'application/sparql-results+xml'}"
            },
        )
    resp.raise_for_status()
    if resp.status_code == 200:
        return resp.text
    return result_string


def result_binding_to_triple(result_binding: dict) -> tuple:
    """Convert a SPARQL result binding to an RDF triple (s, p, o).
    :param result_binding: the SPARQL result binding as a dictionary.
    :returns: a tuple (s, p, o) representing the RDF triple.
    """
    s: URIRef | BNode | None = None
    p: URIRef | None = None
    o: URIRef | BNode | Literal | None = None

    # subject
    s_value = result_binding.get("s", {}).get("value", "")
    s_type = result_binding.get("s", {}).get("type", "")
    if s_type == "uri":
        s = URIRef(s_value)
    elif s_type == "bnode":
        s = BNode(s_value)

    # predicate
    p_value = result_binding.get("p", {}).get("value", "")
    p = URIRef(p_value)

    # object
    o_value = result_binding.get("o", {}).get("value", "")
    o_type = result_binding.get("o", {}).get("type", "")
    if o_type == "uri":
        o = URIRef(o_value)
    elif o_type == "bnode":
        o = BNode(o_value)
    elif o_type == "literal":
        lang = result_binding.get("o", {}).get("xml:lang", None)
        datatype = result_binding.get("o", {}).get("datatype", None)
        if lang:
            o = Literal(o_value, lang=lang)
        elif datatype:
            o = Literal(o_value, datatype=URIRef(datatype))
        else:
            o = Literal(o_value)

    return (s, p, o)


def convert_results_to_graph(results: dict, resource_url: str) -> Graph:
    """Convert SPARQL SELECT query results to an RDF Graph.
    :param results: the SPARQL SELECT query results as a dictionary.
    :param resource_url: the main resource URL to use when subject 's' is missing.
    :returns: an RDF Graph containing the triples.
    """
    g = Graph()
    for row in results.get("results", {}).get("bindings", []):
        try:
            s, p, o = result_binding_to_triple(row)
            if not s:
                # Handle cases where 's' is missing in the row
                g.add((URIRef(resource_url), p, o))
            else:
                g.add((s, p, o))
        except Exception as exc:
            logger.error(str(exc))
    return g


def get_album_art_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[str]:
    """Extracts the album art URL from the RDF graph for the given resource.
    :param rdf_graph: Graph object containing the triples.
    :param resource_url: the main resource for which the album art URL is extracted.
    :returns: URL of the album art as a string, or None if not found.
    """
    try:
        album_art_url = rdf_graph.value(
            subject=URIRef(resource_url),
            predicate=URIRef("https://data.muziekweb.nl/vocab/fullCover"),
        )
        if album_art_url:
            return str(album_art_url)
    except Exception as e:
        logger.exception(f"Error in get_album_art_from_rdf_graph: {str(e)}")
    return None
