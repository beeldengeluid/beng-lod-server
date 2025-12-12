import logging
import json
from flask import render_template, Response
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace._RDF import RDF
from rdflib.namespace._RDFS import RDFS
from rdflib.namespace._SDO import SDO
from rdflib.namespace._SKOS import SKOS
from rdflib.namespace._DCTERMS import DCTERMS
from typing import Optional, List
from util.mime_type_util import MimeType
from util.APIUtil import APIUtil

logger = logging.getLogger()

SKOSXL_NS = "http://www.w3.org/2008/05/skos-xl#"


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


# ========= JSON generator functions for lod-view ==========


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


def generate_html_page(rdf_graph: Graph, resource_iri: str, sparql_endpoint: str):
    logger.info(f"Generating HTML page for {resource_iri}.")
    html_page = get_lod_view_resource(
        rdf_graph,
        resource_iri,
        sparql_endpoint,
    )
    if html_page:
        return Response(html_page, mimetype=MimeType.HTML.value)
    else:
        logger.error(f"Could not generate the HTML page for {resource_iri}.")
        return APIUtil.toErrorResponse(
            "internal_server_error",
            "Could not generate an HTML view for this resource",
        )


def get_lod_view_resource(
    rdf_graph: Graph, resource_url: str, sparql_endpoint: str
) -> str:
    """Handler that, given a Graph and a URI generates an HTML page.
    :param rdf_graph: A Graph for the resource.
    :param resource_url: The URI for the resource.
    """
    if rdf_graph:
        logger.info(
            f"Rendering an html page for graph ({len(rdf_graph)} triples) using template 'resource.html'."
        )
        return render_template(
            "resource.html",
            resource_uri=resource_url,
            structured_data=json_ld_structured_data_for_resource(
                rdf_graph, resource_url
            ),
            json_header=json_header_from_rdf_graph(rdf_graph, resource_url),
            json_iri_iri=json_iri_iri_from_rdf_graph(rdf_graph, resource_url),
            json_iri_lit=json_iri_lit_from_rdf_graph(rdf_graph, resource_url),
            json_iri_bnode=json_iri_bnode_from_rdf_graph(rdf_graph, resource_url),
            nisv_sparql_endpoint=sparql_endpoint,
        )
    return ""


def get_serialised_graph(rdf_graph: Graph, mime_type: MimeType = MimeType.JSON_LD):
    """Generate a response, either the serialized graph or an error response."""
    serialised_graph = rdf_graph.serialize(
        format=mime_type.to_ld_format(), auto_compact=True
    )
    if serialised_graph:
        return Response(serialised_graph, mimetype=mime_type.value, status=200)
    else:
        return APIUtil.toErrorResponse("internal_server_error", "Serialisation failed")
