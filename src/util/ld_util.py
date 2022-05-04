from urllib.parse import urlparse, urlunparse
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, SDO
import requests
import json
from json.decoder import JSONDecodeError
from models.DAANRdfModel import ResourceURILevel
from requests.exceptions import ConnectionError, MissingSchema
from typing import Optional, List
import validators


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


def get_lod_resource_from_rdf_store(resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str) -> Optional[Graph]:
    """Given a resource URI, the data is retrieved from the SPARQL endpoint using a CONSTRUCT query.
    :param resource_url: the resource URI to be retrieved.
    :returns: the RDF data as a GRAPH
    NOTE: Currently, only SDO modelled data in endpoint.
    # TODO: The CONSTRUCT doesn't include 'deeper' triples yet. No SKOS-XL triples, for example.
    """
    if resource_url is None:
        return None
    if sparql_endpoint is None or validators.url(sparql_endpoint) is False:
        return None
    try:
        query_construct = f"CONSTRUCT {{<{resource_url}> ?p ?o }} WHERE {{<{resource_url}> ?p ?o }}"
        resp = requests.get(
            sparql_endpoint, params={"query": query_construct}
        )
        if resp.status_code == 200:
            g = Graph()
            g.parse(data=resp.text, format='xml')
            g.add((URIRef(resource_url), SDO.publisher, URIRef(nisv_organisation_uri)))
            return g
        else:
            print("CONSTRUCT request to sparql server was not successful.")

    except ConnectionError as e:
        print(str(e))
    return None


# Generates the data for the header in resource.html
def json_header_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    try:
        return [
            {
                "o": str(o),
                "namespace": f'{urlparse(str(o)).scheme}://{urlparse(str(o)).netloc}',
                "property": urlparse(str(o)).path.split('/')[-1],
            }
            for o in rdf_graph.objects(subject=URIRef(resource_url), predicate=URIRef(RDF.type))
            if str(rdf_graph.compute_qname(o)[1]) == str(SDO)
        ]
    except Exception:
        print("Error in json_header_from_rdf_graph")
    return None


# Generates part of the LOD view data for resource.html
def json_iri_iri_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> Optional[List[dict]]:
    try: 
        return [
            {
                "namespace": f'{urlparse(str(p)).scheme}://{urlparse(str(p)).netloc}',
                "property": urlparse(str(p)).path.split('/')[-1],
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
                "namespace": f'{urlparse(str(p)).scheme}://{urlparse(str(p)).netloc}',
                "property": urlparse(str(p)).path.split('/')[-1],
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
                bnode_content = []
                for (bnode_prop, bnode_obj) in rdf_graph.predicate_objects(subject=URIRef(o)):
                    bnode_content.append(
                        {
                            "prop": str(bnode_prop),
                            "obj": str(bnode_obj)
                        }
                    )
                json_iri_bnode.append(
                    {
                        "namespace": f'{urlparse(str(p)).scheme}://{urlparse(str(p)).netloc}',
                        "property": urlparse(str(p)).path.split('/')[-1],
                        "p": str(p),
                        "o": bnode_content
                    }
                )
        return json_iri_bnode
    except Exception:
        print("Error in json_iri_bnode_from_rdf_graph")
    return None


def is_public_resource(resource_url: str, sparql_endpoint: str) -> bool:
    """Checks whether the resource is allowed public access by firing a query to the public sparql endpoint.
    :param resource_url: the resource to be checked.
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
