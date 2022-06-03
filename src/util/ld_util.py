from urllib.parse import urlparse, urlunparse

import lxml.etree
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF, RDFS, SDO, SKOS, DCTERMS
import requests
import json
from json.decoder import JSONDecodeError
from models.DAANRdfModel import ResourceURILevel
from requests.exceptions import ConnectionError, MissingSchema
from typing import Optional, List
import validators
from lxml import etree

# declare namespaces
SKOSXL_NS = "http://www.w3.org/2008/05/skos-xl#"
SKOSXL = Namespace(URIRef(SKOSXL_NS))
JUSTSKOS = Namespace(URIRef('http://justskos.org/ns/core#'))
GTAA = Namespace(URIRef('http://data.beeldengeluid.nl/gtaa/'))


def generate_lod_resource_uri(level: ResourceURILevel, identifier: str, beng_data_domain: str) -> Optional[str]:
    """Constructs valid url using the data domain, the level (cat type) and the identifier:
            {Beng data domain}/id/{cat_type}>/{identifier}
    :param level: the cat type
    :param identifier: the DAAN id
    :param beng_data_domain: see BENG_DATA_DOMAIN in settings.py
    :returns: a proper URI as it should be listed in the LOD server.
    """
    if type(level) != ResourceURILevel:
        return None
    url_parts = urlparse(str(beng_data_domain))
    if url_parts.netloc is not None and url_parts.netloc != "":
        path = "/".join(["id", level.value, str(identifier)])
        parts = (url_parts.scheme, url_parts.netloc, path, "", "", "")
        return urlunparse(parts)
    else:
        return None


def get_lod_resource_from_rdf_store(resource_url: str, sparql_endpoint: str,
                                    nisv_organisation_uri: str) -> Optional[Graph]:
    """Given a resource URI, the data is retrieved from the SPARQL endpoint using a CONSTRUCT query.
    Currently, only SDO modelled data in endpoint.
    :param resource_url: the resource URI to be retrieved.
    :param sparql_endpoint: the SPARQL endpoint URL.
    :param nisv_organisation_uri: URI for the publishing organisation.
    :returns: the RDF data as a GRAPH (merged graph for core triples and bnode triples).
    """
    if resource_url is None:
        return None
    if sparql_endpoint is None or validators.url(sparql_endpoint) is False:
        return None
    try:
        g1 = get_triples_for_lod_resource_from_rdf_store(resource_url, sparql_endpoint)
        assert g1 is not None

        g2 = get_preflabels_for_lod_resource_from_rdf_store(resource_url, sparql_endpoint)
        assert g2 is not None

        g3 = get_triples_for_blank_node_from_rdf_store(resource_url, sparql_endpoint)
        assert g3 is not None

        # if SKOS concept get skos xl triples
        if resource_url.startswith('http://data.beeldengeluid.nl/gtaa/'):
            g4 = get_skosxl_label_triples_for_skos_concept_from_rdf_store(resource_url, sparql_endpoint)
            g = g1 + g2 + g3 + g4
        else:
            g = g1 + g2 + g3

        # add the publisher triple (if not already present for teh resource)
        publisher_present = False
        for s, p, o in g.triples((URIRef(resource_url), SDO.publisher, URIRef(nisv_organisation_uri))):
            publisher_present = True
        if publisher_present is not True:
            g.add((URIRef(resource_url), SDO.publisher, URIRef(nisv_organisation_uri)))

        # add the missing namespaces
        g.bind('skosxl', SKOSXL)
        g.bind('justskos', JUSTSKOS)
        g.bind('gtaa', GTAA)

        return g
    except ConnectionError as e:
        print(str(e))
    except AssertionError as e:
        print(str(e))
    return None


def get_triples_for_lod_resource_from_rdf_store(resource_url: str, sparql_endpoint: str) -> Optional[Graph]:
    """Returns a graph with the triples for the LOD resource loaded. Using a construct query to get the triples
     from the rdf store. To be used in association with the other functions that get triples for blank nodes."""
    query_construct = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ " \
                      f"VALUES ?s {{ <{resource_url}> }} ?s ?p ?o FILTER(!ISBLANK(?o)) }}"
    return sparql_construct_query(sparql_endpoint, query_construct)


def get_preflabels_for_lod_resource_from_rdf_store(resource_url: str, sparql_endpoint: str) -> Optional[Graph]:
    """Gets the preflabels for the SKOS Concpets attached to the LOD resource from the rdf store.
    """
    query_construct_pref_labels = f"CONSTRUCT {{ ?s ?p ?o . ?o skos:prefLabel ?pref_label }}" \
                                  f"WHERE {{ VALUES ?s {{ <{resource_url}> }} " \
                                  f"?s ?p ?o FILTER (!ISBLANK(?o)) ?o skos:prefLabel ?pref_label }}"
    return sparql_construct_query(sparql_endpoint, query_construct_pref_labels)


def get_triples_for_blank_node_from_rdf_store(resource_url: str, sparql_endpoint: str) -> Optional[Graph]:
    """Returns a graph with triples for blank nodes attached the LOD resource including preflabels for the
    SKOS Concepts from the rdf store.
    """
    query_construct_bnodes_pref_labels = f"CONSTRUCT {{ ?s ?p ?o . ?o ?y ?z . ?z skos:prefLabel ?pref_label }} " \
                                         f"WHERE {{ VALUES ?s {{ <{resource_url}> }} ?s ?p ?o FILTER ISBLANK(?o) " \
                                         f"?o ?y ?z . ?z skos:prefLabel ?pref_label }}"
    return sparql_construct_query(sparql_endpoint, query_construct_bnodes_pref_labels)


def get_skosxl_label_triples_for_skos_concept_from_rdf_store(resource_url: str, sparql_endpoint: str) -> Optional[
    Graph]:
    """Returns a graph with triples for skos-xl labels for SKOS Concepts from the rdf store.
    resource_url: a SKOS Concept.
    """
    query_construct_skos_xl_labels = f"PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> " \
                                     f"CONSTRUCT {{ ?s ?skos_label ?y . ?y skosxl:literalForm ?literal_form . " \
                                     f"?y a skosxl:Label }} WHERE {{ VALUES ?s {{ <{resource_url}> }} " \
                                     f"?s ?skos_label ?y . ?y a skosxl:Label . ?y skosxl:literalForm ?literal_form }}"
    return sparql_construct_query(sparql_endpoint, query_construct_skos_xl_labels)


def sparql_construct_query(sparql_endpoint: str, query: str) -> Optional[Graph]:
    """Sends a SPARQL CONSTRUCT query to the SPARQL endpoint and returns the result parsed into a Graph.
    """
    try:
        g = Graph()
        resp = requests.get(
            sparql_endpoint, params={"query": query}
        )
        if resp.status_code == 200:
            g.parse(data=resp.text, format='xml')
        else:
            print(f"CONSTRUCT request to sparql server was not successful: {query}")
        return g
    except ConnectionError as e:
        print(str(e))


def json_header_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    """ Generates the data for the header in resource.html"""
    json_header = []
    try:
        json_header = [
            {
                "title": [str(label) for label in rdf_graph[URIRef(resource_url): SKOS.prefLabel]]
                + [str(name) for name in rdf_graph[URIRef(resource_url): SDO.name]]
                + [str(name) for name in rdf_graph[URIRef(resource_url): DCTERMS.title]],
                "o": {
                    "uri": str(o),
                    "prefix": rdf_graph.compute_qname(o)[0],
                    "namespace": str(rdf_graph.compute_qname(o)[1]),
                    "property": rdf_graph.compute_qname(o)[2]
                }
            }
            for o in rdf_graph.objects(subject=URIRef(resource_url), predicate=URIRef(RDF.type))
            if str(rdf_graph.compute_qname(o)[1]) in (str(SDO), str(SKOS))
        ]
    except Exception as e:
        print(f"Error in json_header_from_rdf_graph: {str(e)}")
        print(json_header)
    finally:
        return json_header


def json_iri_iri_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    """Generates part of the LOD view data for resource.html that with: (<uri> <uri> <uri>)"""
    json_iri_iri = []
    try:
        json_iri_iri = [
            {
                "p": {
                    "uri": str(p),
                    "prefix": rdf_graph.compute_qname(p)[0],
                    "namespace": str(rdf_graph.compute_qname(p)[1]),
                    "property": rdf_graph.compute_qname(p)[2],
                },
                "o": {
                    "uri": str(o),
                    "literal_form": [str(lf) for lf in rdf_graph[o: URIRef(f"{SKOSXL_NS}literalForm")]],
                    "prefix": rdf_graph.compute_qname(o)[0],
                    "namespace": str(rdf_graph.compute_qname(o)[1]),
                    "property": rdf_graph.compute_qname(o)[2],
                    "pref_label": [str(label) for label in rdf_graph[o: SKOS.prefLabel]]
                }
            }
            for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if p != RDF.type and isinstance(o, URIRef) and not str(o).endswith('/')
        ]
        # URIs that end with a '/' can not be split by rdflib. Therefore we add them separately.
        for p, o in rdf_graph.predicate_objects(subject=URIRef(resource_url)):
            if isinstance(o, URIRef) and str(o).endswith('/'):
                json_iri_iri += [
                    {
                        "p": {
                            "uri": str(p),
                            "prefix": rdf_graph.compute_qname(p)[0],
                            "namespace": str(rdf_graph.compute_qname(p)[1]),
                            "property": rdf_graph.compute_qname(p)[2],
                        },
                        "o": {
                            "uri": str(o),
                            "literal_form": [],
                            "prefix": '',
                            "namespace": '',
                            "property": '',
                            "pref_label": []
                        }
                    }
                ]
    except Exception as e:
        print(f"Error in json_iri_iri_from_rdf_graph: {str(e)}")
        print(json_iri_iri)
    finally:
        return json_iri_iri


def json_iri_lit_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    """ Generates part of the LOD view data for resource.html (<uri> <uri> literal)"""
    json_iri_lit = []
    try:
        json_iri_lit = [
            {
                "p": {
                    "uri": str(p),
                    "prefix": rdf_graph.compute_qname(p)[0],
                    "namespace": str(rdf_graph.compute_qname(p)[1]),
                    "property": rdf_graph.compute_qname(p)[2]
                },
                "o": {
                    "literal_value": str(o),
                    "datatype": str(o.datatype) if o.datatype is not None else "",
                    "datatype_prefix": rdf_graph.compute_qname(o.datatype)[0] if o.datatype is not None else "",
                    "datatype_namespace": str(rdf_graph.compute_qname(o.datatype)[1]) if o.datatype is not None else "",
                    "datatype_property": rdf_graph.compute_qname(o.datatype)[2] if o.datatype is not None else "",
                }
            }
            for p, o in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if isinstance(o, Literal)
        ]
    except Exception as e:
        print(f"Error in json_iri_lit_from_rdf_graph: {str(e)}")
        print(json_iri_lit)
    finally:
        return json_iri_lit


def json_iri_bnode_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    """Generates part of the LOD view data for resource.html matching: (<uri> <uri> [bnode])"""
    json_iri_bnode = []
    try:
        for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url)):
            if p != RDF.type and isinstance(o, BNode):
                bnode_content = [
                    {
                        "pred": {
                            "uri": str(bnode_pred),
                            "prefix": rdf_graph.compute_qname(bnode_pred)[0],
                            "namespace": str(rdf_graph.compute_qname(bnode_pred)[1]),
                            "property": rdf_graph.compute_qname(bnode_pred)[2]

                        }
                        if isinstance(bnode_pred, URIRef) else {"pred": str(bnode_pred)},

                        "obj": {
                            "uri": str(bnode_obj),
                            "prefix": rdf_graph.compute_qname(bnode_obj)[0],
                            "namespace": str(rdf_graph.compute_qname(bnode_obj)[1]),
                            "property": rdf_graph.compute_qname(bnode_obj)[2],
                            "pref_label": [str(pl) for pl in rdf_graph[bnode_obj: SKOS.prefLabel]]

                        }
                        if isinstance(bnode_obj, URIRef) else {"obj": str(bnode_obj)}
                    }
                    for (bnode_pred, bnode_obj) in rdf_graph.predicate_objects(subject=o)
                    if bnode_obj != RDFS.Resource
                ]
                json_iri_bnode.append(
                    {
                        "p": {
                            "uri": str(p),
                            "prefix": rdf_graph.compute_qname(p)[0],
                            "namespace": str(rdf_graph.compute_qname(p)[1]),
                            "property": rdf_graph.compute_qname(p)[2],
                        },
                        "o": bnode_content
                    }
                )
    except Exception as e:
        print(f"Error in json_iri_bnode_from_rdf_graph: {str(e)}")
        print(json_iri_bnode)
    finally:
        return json_iri_bnode


def is_public_resource(resource_url: str, sparql_endpoint: str) -> bool:
    """Checks whether the resource is allowed public access by sending an ASK query to the public sparql endpoint.
    :param resource_url: the resource to be checked.
    :param sparql_endpoint: the public SPARQL endpoint.
    :return True (yes, public access allowed), False (no, not allowed to dereference)
    """
    if resource_url is None:
        return False
    if sparql_endpoint is None or validators.url(sparql_endpoint) is False:
        return False

    try:
        # get the SPARQL endpoint from the config
        query_ask = "ASK {<%s> ?p ?o . }" % resource_url

        # prepare and get the data from the triple store
        resp = requests.get(  # receives {"head" : {}, "boolean" : true}
            sparql_endpoint, params={"query": query_ask, "format": "json"}
        )
        if resp.status_code == 200:
            json_data = json.loads(resp.text)
            print(json_data)
            return json_data.get("boolean", False) is True
    except ConnectionError as e:
        print(str(e))
    except JSONDecodeError as e:
        print(str(e))
    return False
