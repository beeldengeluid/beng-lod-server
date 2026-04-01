import logging
import requests
import validators
import json
from requests.exceptions import ConnectionError, HTTPError
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF, SDO, SKOS  # type: ignore
from typing import Optional
from urllib.parse import urlparse, urlunparse
from enum import Enum
from models.DatasetApiUriLevel import DatasetApiUriLevel
from models.ResourceApiUriLevel import ResourceApiUriLevel
from config import cfg
import util.ns_util

logger = logging.getLogger()


def generate_lod_resource_uri(
    level: Enum, identifier: str, beng_data_domain: str
) -> str:
    """Constructs valid url using the data domain, the level (cat type or dataset type) and the identifier:
            {Beng data domain}/id/{cat_type}>/{identifier}
    :param level: the cat type
    :param identifier: the DAAN id
    :param beng_data_domain: see BENG_DATA_DOMAIN in settings.py
    :returns: a proper URI as it should be listed in the LOD server.
    """
    if not isinstance(level, DatasetApiUriLevel) and not isinstance(
        level, ResourceApiUriLevel
    ):
        return ""
    url_parts = urlparse(str(beng_data_domain))
    if url_parts.netloc is not None and url_parts.netloc != "":
        path = "/".join(["id", level.value, str(identifier)])
        parts = (url_parts.scheme, url_parts.netloc, path, "", "", "")
        return urlunparse(parts)
    else:
        return ""


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


# ============ Add/remove triples from a graph ===========


def add_publisher(resource_url: str, publisher_uri: str, rdf_graph: Graph):
    """Adds the Organization that publishes the CreativeWork."""
    rdf_graph.add(
        (
            URIRef(resource_url),
            SDO.publisher,
            URIRef(publisher_uri),
        )
    )


def add_structured_data_publisher(
    resource_uri: str, sd_publisher_uri: str, rdf_graph: Graph
):
    """Adds metadata about the structured data to the resource graph."""
    rdf_graph.add(
        (
            URIRef(resource_uri),
            SDO.sdPublisher,
            URIRef(sd_publisher_uri),
        )
    )
    rdf_graph.add(
        (
            URIRef(resource_uri),
            SDO.sdLicense,
            URIRef("https://creativecommons.org/publicdomain/zero/1.0/"),  # CC0 license
        )
    )


def remove_additional_type_skos_concept(resource_uri: str, rdf_graph: Graph):
    """Removes additionalType from the graph if type is already skos:Concept."""
    g = rdf_graph
    skos_concept_type_triple = (
        URIRef(resource_uri),
        RDF.type,
        SKOS.Concept,
    )
    skos_concept_additional_type_triple = (
        URIRef(resource_uri),
        SDO.additionalType,
        SKOS.Concept,
    )
    if skos_concept_type_triple in g and skos_concept_additional_type_triple in g:
        g.remove(skos_concept_additional_type_triple)


# ========== Functions that get data from the RDF store ========


def is_skos_resource(resource_url: str, sparql_endpoint: str) -> bool:
    """Check with the triple store whether the resource exists."""
    query_str = get_query_from_file(cfg.get("BENG_IS_SKOS_RESOURCE", ""))
    query = query_str.replace("?resource_iri", f"<{resource_url}>")
    return sparql_ask_query(sparql_endpoint, query)


def is_nisv_cat_resource(resource_url: str, sparql_endpoint: str) -> bool:
    """Check with the triple store whether the resource exists."""
    query_str = get_query_from_file(cfg.get("BENG_IS_CAT_NISV_RESOURCE", ""))
    query = query_str.replace("?resource_iri", f"<{resource_url}>")
    return sparql_ask_query(sparql_endpoint, query)


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

        # get the results
        query_result = sparql_select_query(sparql_endpoint, query, format="json")
        results = json.loads(query_result)

        # Note we have to add the resource_url for the triples that miss the subject 's'
        g += _convert_results_to_graph(results, resource_url)

        if len(g) == 0:
            logger.error("Graph was empty")
        else:
            # add the publisher triple (if not already present)
            # add_publisher(resource_url, organisation_uri, g)

            # add structured data triples
            add_structured_data_publisher(resource_url, organisation_uri, g)

            # remove sdo:additionalType triple (for skos:Concepts)
            remove_additional_type_skos_concept(resource_url, g)

        # add the missing namespaces and return the graph
        return util.ns_util.bind_namespaces_to_graph(g)

    except ConnectionError as e:
        logger.exception(e)
    except HTTPError as e:
        logger.exception(e)
    return g


def get_inverse_relations_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Given a resource URI, inverse relations ?s ?p <resource_url> are retrieved.
    Given the query, the graph includes labels.
    :param resource_url: the resource URI as object of a relation.
    :param sparql_endpoint: the SPARQL endpoint URL.
    :returns: RDF data as a Graph.
    """
    g = Graph(bind_namespaces="core")
    if not resource_url:
        return g
    if not sparql_endpoint or validators.url(sparql_endpoint) is False:
        return g

    try:
        query_str = get_query_from_file(cfg.get("INVERSE_RELATIONS_QUERY", ""))
        query = query_str.replace("?resource_iri", f"<{resource_url}>")
        query_result = sparql_select_query(sparql_endpoint, query, format="json")
        results = json.loads(query_result)

        # Note we have to add the resource_url for the triples that miss the object 'o'
        g += _convert_inverse_relations_results_to_graph(results, resource_url)

        if len(g) == 0:
            logger.error("Graph was empty")
        else:
            logger.debug(
                f"Graph contains {len(g)} triples for inverse relations of {resource_url}"
            )

        # add the missing namespaces and return the graph
        return util.ns_util.bind_namespaces_to_graph(g)

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


def sparql_construct_query(sparql_endpoint: str, query: str) -> Graph:
    """Sends a SPARQL CONSTRUCT query to the SPARQL endpoint and returns the result parsed into a Graph.
    raises a ConnectionError when the sparql endpoint can not be reached, or
    raises an HTTPError when the request was not successful."""
    g = Graph()
    resp = requests.get(sparql_endpoint, params={"query": query})
    resp.raise_for_status()
    if resp.status_code == 200:
        g.parse(data=resp.text, format="xml")
    return g


def sparql_ask_query(sparql_endpoint: str, query: str) -> bool:
    """Sends a SPARQL ASK query to the SPARQL endpoint and returns True or False.
    raises a ConnectionError when the sparql endpoint can not be reached, or
    raises an HTTPError when the request was not successful."""
    resp = requests.get(sparql_endpoint, params={"query": query, "format": "json"})
    resp.raise_for_status()
    if resp.status_code == 200:
        if resp.json().get("boolean"):
            return True
    return False


def _result_binding_to_triple(result_binding: dict) -> tuple:
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
        if lang is not None:
            o = Literal(o_value, lang=lang)
        elif datatype is not None:
            o = Literal(o_value, datatype=URIRef(datatype))
        else:
            o = Literal(o_value)

    return (s, p, o)


def _convert_results_to_graph(results: dict, resource_url: str) -> Graph:
    """Convert SPARQL SELECT query results to an RDF Graph.
    :param results: the SPARQL SELECT query results as a dictionary.
    :param resource_url: the main resource URL to use when subject 's' is missing.
    :returns: an RDF Graph containing the triples.
    """
    g = Graph()
    for row in results.get("results", {}).get("bindings", []):
        try:
            s, p, o = _result_binding_to_triple(row)
            if not s:
                # Handle cases where 's' is missing in the row
                g.add((URIRef(resource_url), p, o))
            else:
                g.add((s, p, o))
        except Exception as exc:
            logger.error(str(exc))
    return g


def _convert_inverse_relations_results_to_graph(
    results: dict, resource_url: str
) -> Graph:
    """Convert SPARQL SELECT query results to an RDF Graph.
    :param results: the SPARQL SELECT query results as a dictionary.
    :param resource_url: the resource URL to use when object 'o' is missing.
    :returns: an RDF Graph containing the triples.
    """
    g = Graph()
    for row in results.get("results", {}).get("bindings", []):
        try:
            s, p, o = _result_binding_to_triple(row)
            if not o:
                # Handle cases where 'o' is missing in the row
                g.add((s, p, URIRef(resource_url)))
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


def ask_for_inverse_relations(resource_url: str, sparql_endpoint: str) -> bool:
    """Ask the endpoint whether or not there are inverse relations."""
    query_str = get_query_from_file(cfg.get("INVERSE_RELATIONS_ASK", ""))
    query = query_str.replace("?resource_iri", f"<{resource_url}>")
    return sparql_ask_query(sparql_endpoint, query)


# DEBUG FUNCTIONS
# def dump_nt_sorted(g: Graph):
#     lines = g.serialize(format="nt").splitlines()
#     for line in sorted(lines):
#         print(line)
#         # logger.debug(line)


# def check_subgraph_in_graph(subgraph: Graph, big_graph: Graph) -> bool:
#     """Checks if the triples in g1 are included in g2, without checking
#     for isomorphism. To be used for checking if the triples from the separate
#     construct queries in ld_util are included in the graph returned by mw_ld_util.
#     """
#     (in_both, in_first, in_second) = graph_diff_fix(subgraph, big_graph)
#     logger.debug(f"Subgraph contains {len(subgraph)} triples.")
#     if len(subgraph) > 0:
#         if len(in_first) > 0:
#             logger.debug("Subgraph contains triples not in big graph: ")
#             dump_nt_sorted(in_first)
#             # logger.debug("Triples in big graph, but not in subgraph: ")
#             # dump_nt_sorted(in_second)
#             return False
#     return True


# def graph_diff_fix(g1: Graph, g2: Graph) -> tuple[Graph, Graph, Graph]:
#     """workaround for blank node bug in rdflib.compare.graph_diff.
#     The dummy graph contains a blank node, that is added before the comparison
#     and removed from the resulting graph afterwards.
#     """
# from rdflib.compare import graph_diff
#     dummyg = Graph()
#     dummy = URIRef("http://dummy.fix")
#     dummyg.parse(data=" [] <http://dummy.fix> [] . ", format="turtle")
#     b, f, s = graph_diff(g1 + dummyg, g2 + dummyg)
#     #  clean out dummy node
#     for bmn in b.subjects(predicate=dummy):
#         b.remove((bmn, None, None))
#     return (b, f, s)
