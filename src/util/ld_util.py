from urllib.parse import urlparse, urlunparse
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF, RDFS, SDO, SKOS, DCTERMS
import requests
import json
from json.decoder import JSONDecodeError
from models.DAANRdfModel import ResourceURILevel
from requests.exceptions import ConnectionError, HTTPError
from typing import Optional, List
import validators

# declare namespaces
SKOSXL_NS = "http://www.w3.org/2008/05/skos-xl#"
SKOSXL = Namespace(URIRef(SKOSXL_NS))
JUSTSKOS = Namespace(URIRef("http://justskos.org/ns/core#"))
GTAA = Namespace(URIRef("http://data.beeldengeluid.nl/gtaa/"))


def generate_lod_resource_uri(
    level: ResourceURILevel, identifier: str, beng_data_domain: str
) -> Optional[str]:
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


def get_lod_resource_from_rdf_store(
    resource_url: str,
    sparql_endpoint: str,
    nisv_organisation_uri: str,
    named_graph: str = "",
) -> Optional[Graph]:
    """Given a resource URI, the data is retrieved from the SPARQL endpoint using a CONSTRUCT query.
    Currently, only SDO modelled data in endpoint.
    :param resource_url: the resource URI to be retrieved.
    :param sparql_endpoint: the SPARQL endpoint URL.
    :param nisv_organisation_uri: URI for the publishing organisation.
    :param named_graph: URI for the named graph in the SPARQL query.
    :returns: the RDF data as a GRAPH (merged graph for core triples and bnode triples).
    """
    if resource_url is None:
        return None
    if sparql_endpoint is None or validators.url(sparql_endpoint) is False:
        return None
    try:
        g1 = get_triples_for_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, named_graph=named_graph
        )
        g2 = get_preflabels_for_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint
        )
        g3 = get_triples_for_blank_node_from_rdf_store(resource_url, sparql_endpoint)

        # for GTAA SKOS Concepts... get skos xl triples
        if resource_url.startswith("http://data.beeldengeluid.nl/gtaa/"):
            g4 = get_skosxl_label_triples_for_skos_concept_from_rdf_store(
                resource_url, sparql_endpoint
            )
            g5 = get_preflabel_for_gtaa_resource_from_rdf_store(
                resource_url, sparql_endpoint, thes_named_graph=named_graph
            )
            g = g1 + g2 + g3 + g4 + g5
        else:
            g = g1 + g2 + g3

        # the case where there are triples from sparql endpoint
        if len(g) != 0:
            # add the publisher triple (if not already present)
            publisher_triple = (
                URIRef(resource_url),
                SDO.publisher,
                URIRef(nisv_organisation_uri),
            )
            if publisher_triple not in g:
                g.add(publisher_triple)

            # add the missing namespaces
            g.bind("skosxl", SKOSXL)
            g.bind("justskos", JUSTSKOS)
            g.bind("gtaa", GTAA)

        return g
    except ConnectionError as e:
        print(str(e))
    except HTTPError as e:
        print(str(e))
    return None


def get_triples_for_lod_resource_from_rdf_store(
    resource_url: str, sparql_endpoint: str, named_graph: str = ""
) -> Graph:
    """Returns a graph with the triples for the LOD resource loaded. Using a construct query to get the triples
    from the rdf store. To be used in association with the other functions that get triples for blank nodes.
    Note that the named_graph parameter can prevent prefLabels from the catalogue data to end up in the thesaurus."""
    if named_graph != "":
        query_construct = (
            f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ VALUES ?s {{ <{resource_url}> }} "
            f"GRAPH <{named_graph}> {{ ?s ?p ?o FILTER(!ISBLANK(?o)) }} }}"
        )
    else:
        query_construct = (
            f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ VALUES ?s {{ <{resource_url}> }} "
            f"?s ?p ?o FILTER(!ISBLANK(?o)) }}"
        )

    return sparql_construct_query(sparql_endpoint, query_construct)


def get_preflabels_for_lod_resource_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Gets the preflabels for the SKOS Concepts attached to the LOD resource from the rdf store.
    Note: the resource itself is not a SKOS Concept
    """
    query_construct_pref_labels = (
        f"CONSTRUCT {{ ?s ?p ?o . ?o skos:prefLabel ?pref_label }}"
        f"WHERE {{ VALUES ?s {{ <{resource_url}> }} "
        f"?s ?p ?o FILTER (!ISBLANK(?o)) ?o skos:prefLabel ?pref_label }}"
    )
    return sparql_construct_query(sparql_endpoint, query_construct_pref_labels)


def get_preflabel_for_gtaa_resource_from_rdf_store(
    resource_url: str, sparql_endpoint: str, thes_named_graph: str = ""
) -> Graph:
    """Gets the prefLabel, by using 'dumbing down' of the skos-xl prefLabel."""
    query_construct_pref_label_dumbing_down = (
        f"CONSTRUCT {{ ?s skos:prefLabel ?pref_label }} WHERE {{ "
        f"VALUES ?g {{<{thes_named_graph}> }} "
        f"VALUES ?s {{ <{resource_url}> }} "
        f"GRAPH ?g {{ ?s skosxl:prefLabel/skosxl:literalForm ?pref_label }} }}"
    )
    return sparql_construct_query(
        sparql_endpoint, query_construct_pref_label_dumbing_down
    )


def get_triples_for_blank_node_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Returns a graph with triples for blank nodes attached the LOD resource (including preflabels for the
    SKOS Concepts from the rdf store). We need to do that with two separate queries, because ClioPatria doesn't
    support CONSTRUCT queries with UNION.
    """
    # first we get all the triples for the blank nodes...
    query_construct_bnodes = (
        f"CONSTRUCT {{ ?s ?p ?o . ?o ?y ?z }} WHERE {{ VALUES ?s {{ <{resource_url}> }} "
        f"?s ?p ?o FILTER ISBLANK(?o) ?o ?y ?z }}"
    )
    g1 = sparql_construct_query(sparql_endpoint, query_construct_bnodes)

    # .. then we get the preflabels for the concepts...
    query_construct_bnodes_pref_labels = (
        f"CONSTRUCT {{ ?z skos:prefLabel ?pref_label }} WHERE {{ "
        f"VALUES ?s {{ <{resource_url}> }} ?s ?p ?o FILTER ISBLANK(?o) "
        f"?o ?y ?z . ?z skos:prefLabel ?pref_label }}"
    )
    g2 = sparql_construct_query(sparql_endpoint, query_construct_bnodes_pref_labels)

    # ..and after that we merge the two together.
    return g1 + g2


def get_skosxl_label_triples_for_skos_concept_from_rdf_store(
    resource_url: str, sparql_endpoint: str, named_graph: str = ""
) -> Graph:
    """Returns a graph with triples for skos-xl labels for SKOS Concepts from the rdf store.
    :param resource_url: URI of a SKOS Concept.
    :param sparql_endpoint: the location of the RDF store.
    :param named_graph: when the query needs to be filtered add the named_graph.
    """
    if named_graph != "":
        query_construct_skos_xl_labels = (
            f"PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> "
            f"CONSTRUCT {{ ?s ?skos_label ?y . ?y skosxl:literalForm ?literal_form . "
            f"?y a skosxl:Label }} WHERE {{ "
            f"VALUES ?s {{ <{resource_url}> }} "
            f"VALUES ?g {{ <{named_graph}> }} "
            f"GRAPH ?g {{ ?s ?skos_label ?y . ?y a skosxl:Label . "
            f"?y skosxl:literalForm ?literal_form }} }}"
        )
    else:
        query_construct_skos_xl_labels = (
            f"PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> "
            f"CONSTRUCT {{ ?s ?skos_label ?y . ?y skosxl:literalForm ?literal_form . "
            f"?y a skosxl:Label }} WHERE {{ "
            f"VALUES ?s {{ <{resource_url}> }} "
            f"?s ?skos_label ?y . ?y a skosxl:Label . "
            f"?y skosxl:literalForm ?literal_form }}"
        )
    return sparql_construct_query(sparql_endpoint, query_construct_skos_xl_labels)


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


def json_header_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates the data for the header in resource.html"""
    json_header = []
    try:
        json_header = [
            {
                "title": [
                    str(label)
                    for label in rdf_graph.objects(URIRef(resource_url), SKOS.prefLabel)
                ]
                + [
                    str(name)
                    for name in rdf_graph.objects(URIRef(resource_url), SDO.name)
                ]
                + [
                    str(name)
                    for name in rdf_graph.objects(URIRef(resource_url), DCTERMS.title)
                ],
                "o": {
                    "uri": str(o),
                    "prefix": rdf_graph.compute_qname(o)[0],
                    "namespace": str(rdf_graph.compute_qname(o)[1]),
                    "property": rdf_graph.compute_qname(o)[2],
                },
            }
            for o in rdf_graph.objects(
                subject=URIRef(resource_url), predicate=URIRef(RDF.type)
            )
            if str(rdf_graph.compute_qname(o)[1]) in (str(SDO), str(SKOS))
        ]
    except Exception as e:
        print(f"Error in json_header_from_rdf_graph: {str(e)}")
        print(json_header)
    finally:
        return json_header  # noqa: B012 #TODO


def json_iri_iri_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
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
                    "literal_form": [
                        str(lf)
                        for lf in rdf_graph.objects(
                            o, URIRef(f"{SKOSXL_NS}literalForm")
                        )
                    ],
                    "prefix": rdf_graph.compute_qname(o)[0],
                    "namespace": str(rdf_graph.compute_qname(o)[1]),
                    "property": rdf_graph.compute_qname(o)[2],
                    "pref_label": [
                        str(label) for label in rdf_graph.objects(o, SKOS.prefLabel)
                    ],
                },
            }
            for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if p != RDF.type and isinstance(o, URIRef) and not str(o).endswith("/")
        ]
        # URIs that end with a '/' can not be split by rdflib. Therefore we add them separately.
        for p, o in rdf_graph.predicate_objects(subject=URIRef(resource_url)):
            if isinstance(o, URIRef) and str(o).endswith("/"):
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
                            "prefix": "",
                            "namespace": "",
                            "property": "",
                            "pref_label": [],
                        },
                    }
                ]
    except Exception as e:
        print(f"Error in json_iri_iri_from_rdf_graph: {str(e)}")
        print(json_iri_iri)
    finally:
        return json_iri_iri  # noqa: B012 #TODO


def json_iri_lit_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates part of the LOD view data for resource.html (<uri> <uri> literal)"""
    json_iri_lit = []
    try:
        json_iri_lit = [
            {
                "p": {
                    "uri": str(p),
                    "prefix": rdf_graph.compute_qname(p)[0],
                    "namespace": str(rdf_graph.compute_qname(p)[1]),
                    "property": rdf_graph.compute_qname(p)[2],
                },
                "o": {
                    "literal_value": str(o),
                    "datatype": str(o.datatype) if o.datatype is not None else "",
                    "datatype_prefix": rdf_graph.compute_qname(o.datatype)[0]
                    if o.datatype is not None
                    else "",
                    "datatype_namespace": str(rdf_graph.compute_qname(o.datatype)[1])
                    if o.datatype is not None
                    else "",
                    "datatype_property": rdf_graph.compute_qname(o.datatype)[2]
                    if o.datatype is not None
                    else "",
                },
            }
            for p, o in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if isinstance(o, Literal)
        ]
    except Exception as e:
        print(f"Error in json_iri_lit_from_rdf_graph: {str(e)}")
        print(json_iri_lit)
    finally:
        return json_iri_lit  # noqa: B012 #TODO


def json_iri_bnode_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates part of the LOD view data for resource.html matching: (<uri> <uri> [bnode])"""
    # TODO: make sure that we also handle bnodes that have a type and a property with a value.
    json_iri_bnode = []
    try:
        for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url)):
            # print(f"{p}\t{o}")
            if p != RDF.type and isinstance(o, BNode):
                bnode_content = [
                    {
                        "pred": {
                            "uri": str(bnode_pred),
                            "prefix": rdf_graph.compute_qname(bnode_pred)[0],
                            "namespace": str(rdf_graph.compute_qname(bnode_pred)[1]),
                            "property": rdf_graph.compute_qname(bnode_pred)[2],
                        },
                        "obj": {
                            "uri": str(bnode_obj),
                            "prefix": rdf_graph.compute_qname(bnode_obj)[0],
                            "namespace": str(rdf_graph.compute_qname(bnode_obj)[1]),
                            "property": rdf_graph.compute_qname(bnode_obj)[2],
                            "pref_label": [
                                str(pl)
                                for pl in rdf_graph.objects(bnode_obj, SKOS.prefLabel)
                            ],
                        }
                        if isinstance(bnode_obj, URIRef)
                        else str(bnode_obj),
                    }
                    for (bnode_pred, bnode_obj) in rdf_graph.predicate_objects(
                        subject=o
                    )
                    if bnode_obj
                    != RDFS.Resource  # and bnode_pred.property != "associatedMedia"
                ]
                json_iri_bnode.append(
                    {
                        "p": {
                            "uri": str(p),
                            "prefix": rdf_graph.compute_qname(p)[0],
                            "namespace": str(rdf_graph.compute_qname(p)[1]),
                            "property": rdf_graph.compute_qname(p)[2],
                        },
                        "o": bnode_content,
                    }
                )
                # print(f"{p}\t{o}\t{bnode_content}")
    except Exception as e:
        print(f"Error in json_iri_bnode_from_rdf_graph: {str(e)}")
        print(json.dumps(json_iri_bnode, indent=4))
    finally:
        # print(json.dumps(json_iri_bnode, indent=4))
        return json_iri_bnode  # noqa: B012 #TODO


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
