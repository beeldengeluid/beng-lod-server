import logging
import json
from flask import render_template, Response
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace._RDF import RDF
from rdflib.namespace._RDFS import RDFS
from rdflib.namespace._SDO import SDO
from rdflib.namespace._SKOS import SKOS
from rdflib.namespace._DCTERMS import DCTERMS
from rdflib.namespace._OWL import OWL
from typing import Optional, List
from util.mime_type_util import MimeType
from util.APIUtil import APIUtil
import util.mw_ld_util
from util.ns_util import SCHEMA, MUZIEKWEB_VOCAB

logger = logging.getLogger()


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


def json_parts_from_IRI(rdf_graph: Graph, iri: str) -> dict:
    """Generates the parts needed in the UI, eg. prefix, namespace and property."""
    if iri.endswith("/"):  # URIs that end with a '/' can not be split by rdflib.
        return {"uri": iri, "prefix": "", "namespace": "", "property": ""}
    else:
        prefix, namespace, name = rdf_graph.compute_qname(str(iri))
        return {
            "uri": iri,
            "prefix": prefix,
            "namespace": str(namespace),
            "property": name,
        }


def json_label_for_node(
    rdf_graph: Graph, node: URIRef | BNode, lang: str = ""
) -> List[str]:
    """Generates a list of labels for a given IRI or BNode."""
    # TODO: handle language preferences for the UI
    return (
        [
            f"{str(label)} @{Literal(label).language}"
            for label in rdf_graph.objects(node, SKOS.prefLabel)
            if Literal(label).language == lang
        ]
        + [
            str(label)
            for label in rdf_graph.objects(node, SKOS.prefLabel)
            if Literal(label).language and lang == ""
        ]
        + [
            str(name)
            for name in rdf_graph.objects(node, SDO.name)
            if Literal(name).language == lang or lang == ""
        ]
        + [str(title) for title in rdf_graph.objects(node, DCTERMS.title)]
        + [str(label) for label in rdf_graph.objects(node, RDFS.label)]
    )


def json_for_literal(rdf_graph: Graph, literal: Literal, lang: str = "") -> dict:
    """Generates JSON parts for a given Literal."""
    return json_label_for_literal(literal, lang) | json_for_datatype(
        rdf_graph, literal.datatype
    )


def json_for_datatype(rdf_graph: Graph, datatype_iri: URIRef | None) -> dict:
    """Generates JSON parts for a given datatype IRI."""
    if datatype_iri:
        prefix, namespace, name = rdf_graph.compute_qname(str(datatype_iri))
        return {
            "datatype": {
                "uri": str(datatype_iri),
                "prefix": prefix,
                "namespace": str(namespace),
                "property": name,
            }
        }
    else:
        return {}


def json_label_for_literal(literal: Literal, lang: str = "") -> dict:
    """Generates a list of labels for a given Literal.
    A language preference can be given.
    """
    return {
        "labels": [
            (
                f"{str(literal)} @{literal.language}"
                if literal.language and literal.language == lang
                else (
                    f"{str(literal)} @{literal.language}"
                    if literal.language and lang == ""
                    else str(literal)
                )
            )
        ]
    }

    # | json_for_datatype(literal.graph, literal.datatype)

    # return {
    #     "literal_value": f"{str(literal)} @{literal.language}"
    #         if literal.language and literal.language == lang else f"{str(literal)} @{literal.language}"if literal.language and lang == "" else str(literal) if lang == ""
    # } | json_for_datatype(rdf_graph, literal.datatype)


def json_header_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates the JSON data for the header in lodview."""
    json_header = []
    try:
        json_header = [
            {
                "title": json_label_for_node(
                    rdf_graph, URIRef(resource_url), lang="nl"
                ),
                "o": json_parts_from_IRI(rdf_graph, str(o)),
            }
            for o in rdf_graph.objects(
                subject=URIRef(resource_url), predicate=URIRef(RDF.type)
            )
            if json_parts_from_IRI(rdf_graph, str(o)).get("namespace", "")
            in (str(SDO), str(SKOS), str(SCHEMA), str(MUZIEKWEB_VOCAB), str(OWL))
        ]
        return json_header
    except Exception as e:
        logger.exception(f"Error in json_header_from_rdf_graph: {str(e)}")
        logger.error(json_header)
    return json_header


def json_iri_iri_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates JSON data (<uri> <uri> <uri>) for the LOD view."""
    json_iri_iri = []
    try:
        json_iri_iri = [
            {
                "p": json_parts_from_IRI(rdf_graph, str(p)),
                "o": json_parts_from_IRI(rdf_graph, str(o))
                | {"labels": json_label_for_node(rdf_graph, o)},
            }
            for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if isinstance(o, URIRef)  # p != RDF.type and
        ]
        return json_iri_iri
    except Exception as e:
        logger.exception(f"Error in json_iri_iri_from_rdf_graph: {str(e)}")
        logger.error(json_iri_iri)
    return json_iri_iri


def json_iri_lit_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates JSON structured data (<uri> <uri> literal) to be used in the LOD view templates."""
    json_iri_lit = []
    try:
        json_iri_lit = [
            {
                "p": json_parts_from_IRI(rdf_graph, str(p)),
                "o": (
                    json_label_for_literal(o)
                    if o.datatype is None
                    else json_label_for_literal(o)
                    | json_for_datatype(rdf_graph, o.datatype)
                ),
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
                        "pred": json_parts_from_IRI(rdf_graph, str(bnode_pred)),
                        "obj": (
                            json_parts_from_IRI(rdf_graph, str(bnode_obj))
                            | {"labels": json_label_for_node(rdf_graph, bnode_obj)}
                            if isinstance(bnode_obj, URIRef)
                            else (
                                json_for_literal(rdf_graph, bnode_obj)
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
                        "p": json_parts_from_IRI(rdf_graph, str(p)),
                        "o": bnode_content,
                    }
                )
        return json_iri_bnode
    except Exception as e:
        logger.exception(f"Error in json_iri_bnode_from_rdf_graph: {str(e)}")
        logger.error(json.dumps(json_iri_bnode, indent=4))
    return json_iri_bnode


def generate_html_page(
    rdf_graph: Graph,
    resource_iri: str,
    sparql_endpoint: str,
    template: str = "resource.html",
):
    logger.info(f"Generating HTML page for {resource_iri}.")
    html_page = get_lod_view_resource(
        rdf_graph,
        resource_iri,
        sparql_endpoint,
        html_template=template,
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
    rdf_graph: Graph,
    resource_url: str,
    sparql_endpoint: str,
    html_template: str = "resource.html",
) -> str:
    """Given a Graph, a URI and an HTML template, return an HTML page.
    :param rdf_graph: A Graph for the resource.
    :param resource_url: The URI for the resource.
    :param sparql_endpoint: The SPARQL endpoint URL.
    :param html_template: The HTML template to be used.
    :returns: rendered HTML page as string.
    """
    if rdf_graph:
        logger.info(
            f"Rendering an html page for graph ({len(rdf_graph)} triples) using template '{html_template}'."
        )
        return render_template(
            html_template,
            resource_uri=resource_url,
            structured_data=json_ld_structured_data_for_resource(
                rdf_graph, resource_url
            ),
            json_header=json_header_from_rdf_graph(rdf_graph, resource_url),
            json_iri_iri=json_iri_iri_from_rdf_graph(rdf_graph, resource_url),
            json_iri_lit=json_iri_lit_from_rdf_graph(rdf_graph, resource_url),
            json_iri_bnode=json_iri_bnode_from_rdf_graph(rdf_graph, resource_url),
            sparql_endpoint=sparql_endpoint,
            album_art=util.mw_ld_util.get_album_art_from_rdf_graph(
                rdf_graph, resource_url
            ),
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


def get_lod_view_resource_header(
    rdf_graph_header_json: List[dict], resource_uri: str
) -> str:
    """Given a list of dicts containing the header information for the lod view page,
    a call to flask's render_template renders the template and outputs (partial HTML).
    This output is included in the lod view page.
    """
    return render_template(
        "resource_lod_view_header.html",
        resource_uri=resource_uri,
        rdf_graph_header_json=rdf_graph_header_json,
    )
