from urllib.parse import urlparse, urlunparse

import lxml.etree
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, SDO, split_uri
import requests
import json
from json.decoder import JSONDecodeError
from models.DAANRdfModel import ResourceURILevel
from requests.exceptions import ConnectionError, MissingSchema
from typing import Optional, List
import validators
from lxml import etree


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


def get_lod_resource_from_rdf_store(resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str) -> Optional[
    Graph]:
    """Given a resource URI, the data is retrieved from the SPARQL endpoint using a CONSTRUCT query.
    :param resource_url: the resource URI to be retrieved.
    :param sparql_endpoint: the SPARQL endpoint URL
    :param nisv_organisation_uri: URI for the publishing organisation
    :returns: the RDF data as a GRAPH (merged graph for core triples and bnode triples)
    NOTE: Currently, only SDO modelled data in endpoint.
    """
    if resource_url is None:
        return None
    if sparql_endpoint is None or validators.url(sparql_endpoint) is False:
        return None
    try:
        # first get triples that have not a blank node as object in g1
        g1 = Graph()
        query_construct = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ " \
                          f"VALUES ?s {{ <{resource_url}> }} ?s ?p ?o FILTER(!ISBLANK(?o)) }}"
        resp = requests.get(
            sparql_endpoint, params={"query": query_construct}
        )
        if resp.status_code == 200:
            g1.parse(data=resp.text, format='xml')
            g1.add((URIRef(resource_url), SDO.publisher, URIRef(nisv_organisation_uri)))
        else:
            print("CONSTRUCT request to sparql server was not successful.")

        # then store the triples for the blank nodes in g2
        g2 = Graph()
        query_construct_bnodes = f"CONSTRUCT {{ ?s ?p ?o . ?o ?y ?z }} WHERE {{ " \
                                 f"VALUES ?s {{ <{resource_url}> }} ?s ?p ?o FILTER ISBLANK(?o) ?o ?y ?z }}"
        resp = requests.get(
            sparql_endpoint, params={"query": query_construct_bnodes}
        )
        if resp.status_code == 200:
            g2.parse(data=resp.text, format='xml')
        else:
            print("CONSTRUCT request to sparql server was not successful.")

        g = g1 + g2  # the merged graphs
        return g
    except ConnectionError as e:
        print(str(e))
    return None


def json_header_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    """ Generates the data for the header in resource.html"""
    try:
        return [
            {
                "o": str(o),
                "namespace": split_uri(o)[0],  # f'{urlparse(str(o)).scheme}://{urlparse(str(o)).netloc}',
                "property": split_uri(o)[1],  # urlparse(str(o)).path.split('/')[-1],
            }
            for o in rdf_graph.objects(subject=URIRef(resource_url), predicate=URIRef(RDF.type))
            if split_uri(o)[0] == str(SDO)
        ]
    except Exception:
        print("Error in json_header_from_rdf_graph")
    return None


# Generates part of the LOD view data for resource.html
def json_iri_iri_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    try:
        return [
            {
                "namespace": split_uri(p)[0],
                "property": split_uri(p)[1],
                "p": str(p),
                "o": str(o)
            }
            for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if p != RDF.type and isinstance(o, URIRef)
        ]
    except Exception:
        print("Error in json_iri_iri_from_rdf_graph")
    return None


# Generates part of the LOD view data for resource.html
def json_iri_lit_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    try:
        return [
            {
                "namespace": split_uri(p)[0],
                "property": split_uri(p)[1],
                "p": str(p),
                "o": str(o),
                "type_o": str(o.datatype.n3(rdf_graph.namespace_manager))
            }
            for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if p != RDF.type and isinstance(o, Literal)
        ]
    except Exception:
        print("Error in json_iri_iri_from_rdf_graph")
    return None


# Generates part of the LOD view data for resource.html
def json_iri_bnode_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    json_iri_bnode = []
    try:
        for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url)):
            if p != RDF.type and isinstance(o, BNode):
                bnode_content = [
                    {
                        "pred": {
                            "namespace": split_uri(bnode_pred)[0],
                            "property": split_uri(bnode_pred)[1],
                            "uri": str(bnode_pred)
                        }
                        if isinstance(bnode_pred, URIRef) else str(bnode_pred),

                        "obj": {
                            "namespace": split_uri(bnode_obj)[0],
                            "property": split_uri(bnode_obj)[1],
                            "uri": str(bnode_obj)
                        }
                        if isinstance(bnode_obj, URIRef) else str(bnode_obj)
                    }
                    for (bnode_pred, bnode_obj) in rdf_graph.predicate_objects(subject=o)
                    if bnode_obj != RDFS.Resource
                ]
                json_iri_bnode.append(
                    {
                        "namespace": split_uri(p)[0],
                        "property": split_uri(p)[1],
                        "p": str(p),
                        "o": bnode_content
                    }
                )
        return json_iri_bnode
    except Exception:
        print("Error in json_iri_bnode_from_rdf_graph")
    return None


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
