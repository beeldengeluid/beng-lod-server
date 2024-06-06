from datetime import datetime
import json
import logging
import requests
import validators

from requests.exceptions import ConnectionError, HTTPError
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF, RDFS, SDO, SKOS, DCTERMS, XSD
from typing import Optional, List
from urllib.parse import urlparse, urlunparse

from enum import Enum
from models.DatasetApiUriLevel import DatasetApiUriLevel
from models.ResourceApiUriLevel import ResourceApiUriLevel

logger = logging.getLogger()

# declare namespaces
SKOSXL_NS = "http://www.w3.org/2008/05/skos-xl#"
SKOSXL = Namespace(URIRef(SKOSXL_NS))
GTAA = Namespace(URIRef("http://data.beeldengeluid.nl/gtaa/"))
SDOTORG = "https://schema.org/"
BENGTHES = "http://data.beeldengeluid.nl/schema/thes#"
WIKIDATA = "http://www.wikidata.org/entity/"
SKOS_NS = "http://www.w3.org/2004/02/skos/core#"
DCTERMS_NS = "http://purl.org/dc/terms/"
DISCOGS = "https://api.discogs.com/artists/"


def generate_lod_resource_uri(
    level: Enum, identifier: str, beng_data_domain: str
) -> Optional[str]:
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
        return None
    url_parts = urlparse(str(beng_data_domain))
    if url_parts.netloc is not None and url_parts.netloc != "":
        path = "/".join(["id", level.value, str(identifier)])
        parts = (url_parts.scheme, url_parts.netloc, path, "", "", "")
        return urlunparse(parts)
    else:
        return None


############# Add/remove triples from a graph ###################


def add_publisher(resource_url: str, publisher_uri: str, rdf_graph: Graph):
    """Adds the Organization that publishes the CreativeWork."""
    g = rdf_graph
    publisher_triple = (
        URIRef(resource_url),
        SDO.publisher,
        URIRef(publisher_uri),
    )
    if publisher_triple not in g:
        g.add(publisher_triple)


def add_structured_data_publisher(
    resource_uri: str, sd_publisher_uri: str, rdf_graph: Graph
):
    """Adds metadata about the structured data to the resource graph."""
    g = rdf_graph
    sdPublisher_triple = (
        URIRef(resource_uri),
        SDO.sdPublisher,
        URIRef(sd_publisher_uri),
    )
    g.add(sdPublisher_triple)

    cc0_license_uri = "https://creativecommons.org/publicdomain/zero/1.0/"
    sd_license_triple = (
        URIRef(resource_uri),
        SDO.sdLicense,
        URIRef(cc0_license_uri),
    )
    g.add(sd_license_triple)

    sd_date_published_triple = (
        URIRef(resource_uri),
        SDO.sdDatePublished,
        Literal(datetime.now().isoformat(timespec="seconds"), datatype=XSD.datetime),
    )
    g.add(sd_date_published_triple)


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


############### Functions that get data from the RDF store ##############


def get_lod_resource_from_rdf_store(
    resource_url: str,
    sparql_endpoint: str,
    nisv_organisation_uri: str,
) -> Optional[Graph]:
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
        g = Graph(bind_namespaces="core")
        g += get_triples_for_lod_resource_from_rdf_store(resource_url, sparql_endpoint)
        g += get_triple_for_is_part_of_relation(resource_url, sparql_endpoint)
        g += get_preflabels_and_type_for_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint
        )
        g += get_label_triples_and_types_for_entities_and_roles_from_rdf_store(
            resource_url, sparql_endpoint
        )
        g += get_triples_for_blank_node_from_rdf_store(resource_url, sparql_endpoint)
        g += get_label_for_parent(resource_url, sparql_endpoint)
        g += get_label_for_has_part(resource_url, sparql_endpoint)
        g += get_label_for_is_part_of_program(resource_url, sparql_endpoint)

        # for GTAA SKOS Concepts... get skos xl triples
        if resource_url.startswith("http://data.beeldengeluid.nl/gtaa/"):
            g += get_skosxl_label_triples_for_skos_concept_from_rdf_store(
                resource_url, sparql_endpoint
            )
            g += get_preflabel_for_gtaa_resource_from_rdf_store(
                resource_url, sparql_endpoint
            )

        if len(g) == 0:
            logger.error("Graph was empty")
            return None
        else:
            # add the publisher triple (if not already present)
            add_publisher(resource_url, nisv_organisation_uri, g)

            # add structured data triples
            add_structured_data_publisher(resource_url, nisv_organisation_uri, g)

            # remove sdo:additionalType triple (for skos:Concepts)
            remove_additional_type_skos_concept(resource_url, g)

        # add the missing namespaces
        g.bind("skosxl", SKOSXL)
        g.bind("gtaa", GTAA)
        g.bind("sdo", SDOTORG)
        g.bind("bengthes", BENGTHES)
        g.bind("wd", WIKIDATA)
        g.bind("skos", SKOS_NS)
        g.bind("dcterms", DCTERMS_NS)
        g.bind("discogs", DISCOGS)

        return g
    except ConnectionError as e:
        logger.exception(e)
    except HTTPError as e:
        logger.exception(e)
    return None


def get_triples_for_lod_resource_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Returns a graph with the triples for the LOD resource loaded, using a construct
    query to get the triples from the rdf store.
    To be used in association with the other functions that get triples for blank nodes.
    """
    query_construct = (
        f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ VALUES ?s {{ <{resource_url}> }} "
        f"?s ?p ?o FILTER(!ISBLANK(?o)) FILTER(?p != skos:prefLabel) FILTER(?p != dcterms:dateAvailable)}}"
    )

    return sparql_construct_query(sparql_endpoint, query_construct)


def get_preflabels_and_type_for_lod_resource_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Gets the preflabels for the SKOS Concepts linked to the LOD resource.
    The labels are derived from the SKOSXL labels in the thesaurus graph in the
    RDF store. Acquiring preferred labels this way, is referred to as 'dumbing down'.
    Also retrieves the type and, if available, additionalType of the concept
    """
    # first the labels and type
    query_construct_pref_labels = (
        f"CONSTRUCT {{ ?s ?p ?o . ?o skos:prefLabel ?pref_label . ?o rdf:type ?t}}"
        f"WHERE {{ VALUES ?s {{ <{resource_url}> }} "
        f'?s ?p ?o FILTER (!ISBLANK(?o)) ?o skosxl:prefLabel/skosxl:literalForm ?pref_label .?o rdf:type ?t FILTER(LANG(?pref_label) = "nl") }}'
    )
    g = sparql_construct_query(sparql_endpoint, query_construct_pref_labels)

    # then the additional type
    query_construct_additional_type = (
        f"CONSTRUCT {{ ?s ?p ?o . ?o sdo:additionalType ?t}}"
        f"WHERE {{ VALUES ?s {{ <{resource_url}> }} "
        f"?s ?p ?o FILTER (!ISBLANK(?o)) . ?o sdo:additionalType ?t }}"
    )
    g += sparql_construct_query(sparql_endpoint, query_construct_additional_type)

    return g


def get_preflabel_for_gtaa_resource_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Gets the prefLabel, by using 'dumbing down' of the skos-xl prefLabel"""

    # first the pref label and type
    query_construct_pref_label_dumbing_down = (
        f"CONSTRUCT {{ ?s skos:prefLabel ?pref_label}} WHERE {{ "
        f"VALUES ?s {{ <{resource_url}> }} "
        f"GRAPH ?g {{ ?s skosxl:prefLabel/skosxl:literalForm ?pref_label}} }}"
    )
    return sparql_construct_query(
        sparql_endpoint, query_construct_pref_label_dumbing_down
    )


def get_triples_for_blank_node_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Returns a graph with triples for blank nodes attached to the LOD resource
    (including preflabels for the SKOS Concepts from the rdf store). We need
    to do that with two separate queries, because ClioPatria doesn't support
    CONSTRUCT queries with UNION.
    """
    # first we get all the triples for the blank nodes...
    query_construct_bnodes = (
        f"CONSTRUCT {{ ?s ?p ?o . ?o ?y ?z }} WHERE {{ VALUES ?s {{ <{resource_url}> }} "
        f"?s ?p ?o FILTER ISBLANK(?o) ?o ?y ?z }}"
    )
    g = sparql_construct_query(sparql_endpoint, query_construct_bnodes)

    # .. then we get the preflabels for the concepts...
    query_construct_bnodes_pref_labels = (
        f"CONSTRUCT {{ ?z skos:prefLabel ?pref_label }} WHERE {{ "
        f"VALUES ?s {{ <{resource_url}> }} ?s ?p ?o FILTER ISBLANK(?o) "
        f"?o ?y ?z . ?z skos:prefLabel ?pref_label }}"
    )
    g += sparql_construct_query(sparql_endpoint, query_construct_bnodes_pref_labels)

    return g


def get_label_triples_and_types_for_entities_and_roles_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Returns a graph with label triples for the labels of entities
     and roles attached to the LOD resource
    (including preflabels for the SKOS Concepts from the rdf store).
    """
    # get the preflabels and types for the entities...
    query_construct_person_pref_labels = (
        f"PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> "
        f"CONSTRUCT {{ ?z skos:prefLabel ?pref_label . ?z rdf:type ?t }} WHERE {{ "
        f"VALUES ?s {{ <{resource_url}> }} . ?s ((sdo:creator/sdo:creator)|(sdo:byArtist/sdo:byArtist)|(sdo:actor/sdo:actor)|(sdo:contributor/sdo:contributor)|(sdo:mentions/sdo:mentions)|(sdo:productionCompany/sdo:productionCompany)) ?z . ?z skosxl:prefLabel/skosxl:literalForm ?pref_label .?z rdf:type ?t }}"
    )
    g = sparql_construct_query(sparql_endpoint, query_construct_person_pref_labels)

    # get the additional types for the entities...
    query_construct_person_pref_labels = (
        f"PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> "
        f"CONSTRUCT {{ ?z skos:prefLabel ?pref_label . ?z sdo:additionalType ?t}} WHERE {{ "
        f"VALUES ?s {{ <{resource_url}> }} . ?s ((sdo:creator/sdo:creator)|(sdo:byArtist/sdo:byArtist)|(sdo:actor/sdo:actor)|(sdo:contributor/sdo:contributor|(sdo:mentions/sdo:mentions)|(sdo:productionCompany/sdo:productionCompany))) ?z . ?z skosxl:prefLabel/skosxl:literalForm ?pref_label .?z sdo:additionalType ?t}}"
    )
    g += sparql_construct_query(sparql_endpoint, query_construct_person_pref_labels)
    # get the rdfs labels and types for the roles...
    query_construct_role_pref_labels = (
        f"CONSTRUCT {{ ?z rdfs:label ?label . ?z rdf:type ?t }} WHERE {{ "
        f"VALUES ?s {{ <{resource_url}> }} . ?s (sdo:creator|sdo:byArtist|sdo:actor|sdo:contributor|sdo:mentions|sdo:productionCompany)/sdo:roleName ?z . ?z rdfs:label ?label . ?z rdf:type ?t }}"
    )
    g += sparql_construct_query(sparql_endpoint, query_construct_role_pref_labels)

    return g


def get_skosxl_label_triples_for_skos_concept_from_rdf_store(
    resource_url: str, sparql_endpoint: str
) -> Graph:
    """Returns a graph with triples for skos-xl labels for SKOS Concepts from the rdf store.
    :param resource_url: URI of a SKOS Concept.
    :param sparql_endpoint: the location of the RDF store.
    """
    query_construct_skos_xl_labels = (
        f"PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> "
        f"CONSTRUCT {{ ?s ?skos_label ?y . ?y skosxl:literalForm ?literal_form . "
        f"?y a skosxl:Label }} WHERE {{ "
        f"VALUES ?s {{ <{resource_url}> }} "
        f"?s ?skos_label ?y . ?y a skosxl:Label . "
        f"?y skosxl:literalForm ?literal_form }}"
    )
    return sparql_construct_query(sparql_endpoint, query_construct_skos_xl_labels)


def get_triple_for_is_part_of_relation(
    resource_uri: str, sparql_endpoint: str
) -> Graph:
    """Only applicable for sdo:Clip. Adds the sdo:isPartOf relation, making it possible
    to refer back (upwards) to the program from a scene.
    Note: Only the inverse of this relation is available in the triple store.
    """
    query_construct_triple_for_part_of = (
        f"CONSTRUCT {{  ?clip sdo:isPartOf ?program }}"
        f"WHERE {{ VALUES ?clip {{<{resource_uri}>}} ?program sdo:hasPart ?clip }}"
    )
    return sparql_construct_query(sparql_endpoint, query_construct_triple_for_part_of)


def get_label_for_is_part_of_program(resource_uri: str, sparql_endpoint: str) -> Graph:
    """Returns a graph with the triple for the label/title for the program
    that a scene is part of with sdo:isPartOf relation.
    """
    query_construct_label_for_program = (
        f"CONSTRUCT {{ ?program sdo:name ?program_name }}"
        f"WHERE {{ ?program sdo:hasPart <{resource_uri}> "
        f"OPTIONAL {{ ?program sdo:name ?p_name }}"
        f'BIND( COALESCE( IF(?p_name, ?p_name, 1/0), "UNTITLED"^^xsd:string )'
        f" AS ?program_name)}}"
    )
    return sparql_construct_query(sparql_endpoint, query_construct_label_for_program)


def get_label_for_parent(resource_uri: str, sparql_endpoint: str) -> Graph:
    """Returns a graph with the triple for the label/title of the parent object."""
    query_construct_labels_for_parent = (
        f"CONSTRUCT {{ ?o sdo:name ?parent_name }}"
        f"WHERE {{ <{resource_uri}> (sdo:partOfSeries|sdo:partOfSeason|sdo:includedInDataCatalog|^sdo:distribution) ?o FILTER(!ISBLANK(?o)) "
        f"OPTIONAL {{ ?o sdo:name ?o_name }}"
        f'BIND( COALESCE( IF(STR(?o_name), STR(?o_name), 1/0), "UNTITLED"^^xsd:string )'
        f" AS ?parent_name)}}"
    )
    return sparql_construct_query(sparql_endpoint, query_construct_labels_for_parent)


def get_label_for_has_part(resource_uri: str, sparql_endpoint: str) -> Graph:
    """Returns a graph with the triples for the label/title for sdo:hasPart"""
    query_construct_labels_for_has_part = (
        f"CONSTRUCT {{ ?o sdo:name ?part_name }}"
        f"WHERE {{ <{resource_uri}> (sdo:hasPart|sdo:dataset|sdo:distribution) ?o FILTER(!ISBLANK(?o)) "
        f"OPTIONAL {{ ?o sdo:name ?o_name }}"
        f'BIND( COALESCE( IF(STR(?o_name), STR(?o_name), 1/0), "UNTITLED"^^xsd:string )'
        f" AS ?part_name)}}"
    )
    return sparql_construct_query(sparql_endpoint, query_construct_labels_for_has_part)


def json_ld_structured_data_for_resource(rdf_graph: Graph, resource_url: str) -> str:
    """Returns a serialized graph in JSON_LD format with triples for the resource.
    :param rdf_graph: Graph object containing the triples.
    :param resource_url: the main resource for which the structured data is returned.
    """
    return rdf_graph.serialize(
        format="json-ld",
        context=dict(rdf_graph.namespaces()),
        auto_compact=True,
    )


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


######### JSON generator functions for lod-view ###############


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
                    if Literal(label).language == "nl"
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
                    "prefix": rdf_graph.compute_qname(str(o))[0],
                    "namespace": str(rdf_graph.compute_qname(str(o))[1]),
                    "property": rdf_graph.compute_qname(str(o))[2],
                },
            }
            for o in rdf_graph.objects(
                subject=URIRef(resource_url), predicate=URIRef(RDF.type)
            )
            if str(rdf_graph.compute_qname(str(o))[1]) in (str(SDO), str(SKOS))
        ]
        return json_header
    except Exception as e:
        logger.exception(f"Error in json_header_from_rdf_graph: {str(e)}")
        logger.error(json_header)
    return json_header


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
                    "prefix": rdf_graph.compute_qname(str(p))[0],
                    "namespace": str(rdf_graph.compute_qname(str(p))[1]),
                    "property": rdf_graph.compute_qname(str(p))[2],
                },
                "o": {
                    "uri": str(o),
                    "literal_form": [
                        f"{str(lf)} @{Literal(lf).language}"
                        for lf in rdf_graph.objects(
                            o, URIRef(f"{SKOSXL_NS}literalForm")
                        )
                    ],
                    "prefix": rdf_graph.compute_qname(str(o))[0],
                    "namespace": str(rdf_graph.compute_qname(str(o))[1]),
                    "property": rdf_graph.compute_qname(str(o))[2],
                    "pref_label": [
                        str(label)
                        for label in rdf_graph.objects(o, SKOS.prefLabel)
                        if Literal(label).language == "nl"
                    ],
                    "parent_label": [
                        str(label) for label in rdf_graph.objects(o, SDO.name)
                    ],
                    "part_label": [
                        str(label) for label in rdf_graph.objects(o, SDO.name)
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
                            "prefix": rdf_graph.compute_qname(str(p))[0],
                            "namespace": str(rdf_graph.compute_qname(str(p))[1]),
                            "property": rdf_graph.compute_qname(str(p))[2],
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
        return json_iri_iri
    except Exception as e:
        logger.exception(f"Error in json_iri_iri_from_rdf_graph: {str(e)}")
        logger.error(json_iri_iri)
    return json_iri_iri


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
                    "prefix": rdf_graph.compute_qname(str(p))[0],
                    "namespace": str(rdf_graph.compute_qname(str(p))[1]),
                    "property": rdf_graph.compute_qname(str(p))[2],
                },
                "o": {
                    "literal_value": (
                        f"{str(o)} @{o.language}" if o.language else f"{str(o)}"
                    ),
                    "datatype": str(o.datatype) if o.datatype is not None else "",
                    "datatype_prefix": (
                        rdf_graph.compute_qname(str(o.datatype))[0]
                        if o.datatype is not None
                        else ""
                    ),
                    "datatype_namespace": (
                        str(rdf_graph.compute_qname(str(o.datatype))[1])
                        if o.datatype is not None
                        else ""
                    ),
                    "datatype_property": (
                        rdf_graph.compute_qname(str(o.datatype))[2]
                        if o.datatype is not None
                        else ""
                    ),
                },
            }
            for p, o in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if isinstance(o, Literal)
        ]
        return json_iri_lit
    except Exception as e:
        logger.exception(f"Error in json_iri_lit_from_rdf_graph: {str(e)}")
        logger.error(json_iri_lit)
    return json_iri_lit


def json_iri_bnode_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates part of the LOD view data for resource.html matching: (<uri> <uri> [bnode])"""
    # TODO: make sure that we also handle bnodes that have a type and a property with a value.
    json_iri_bnode = []
    try:
        for p, o in rdf_graph.predicate_objects(subject=URIRef(resource_url)):
            if p != RDF.type and isinstance(o, BNode):
                bnode_content = [
                    {
                        "pred": {
                            "uri": str(bnode_pred),
                            "prefix": rdf_graph.compute_qname(str(bnode_pred))[0],
                            "namespace": str(
                                rdf_graph.compute_qname(str(bnode_pred))[1]
                            ),
                            "property": rdf_graph.compute_qname(str(bnode_pred))[2],
                        },
                        "obj": (
                            {
                                "uri": str(bnode_obj),
                                "prefix": rdf_graph.compute_qname(str(bnode_obj))[0],
                                "namespace": str(
                                    rdf_graph.compute_qname(str(bnode_obj))[1]
                                ),
                                "property": rdf_graph.compute_qname(str(bnode_obj))[2],
                                "pref_label": [
                                    f"{str(pl)} @{Literal(pl).language}"
                                    for pl in rdf_graph.objects(
                                        bnode_obj, SKOS.prefLabel
                                    )
                                ],
                            }
                            if isinstance(bnode_obj, URIRef)
                            else (
                                {
                                    "label": (
                                        f"{str(bnode_obj)} @{bnode_obj.language}"
                                        if bnode_obj.language
                                        else f"{str(bnode_obj)}"
                                    )
                                }
                                if isinstance(bnode_obj, Literal)
                                else str(bnode_obj)
                            )
                        ),
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
                            "prefix": rdf_graph.compute_qname(str(p))[0],
                            "namespace": str(rdf_graph.compute_qname(str(p))[1]),
                            "property": rdf_graph.compute_qname(str(p))[2],
                        },
                        "o": bnode_content,
                    }
                )
        return json_iri_bnode
    except Exception as e:
        logger.exception(f"Error in json_iri_bnode_from_rdf_graph: {str(e)}")
        logger.error(json.dumps(json_iri_bnode, indent=4))
    return json_iri_bnode
