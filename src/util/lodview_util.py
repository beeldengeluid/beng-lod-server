import itertools
import logging
import json
from collections import Counter
from flask import render_template, Response
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, SDO, SKOS, DCTERMS, OWL  # type: ignore
from typing import Optional, List
from util.mime_type_util import MimeType
from util.APIUtil import APIUtil
import util.ld_util
from util.ns_util import SCHEMA, MUZIEKWEB_VOCAB, SKOSXL
from config import cfg

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
            "prefix": prefix if not prefix.startswith("ns") else "",
            "namespace": str(namespace),
            "property": name,
        }


def json_label_for_node(
    rdf_graph: Graph, node: URIRef | BNode, lang: str = ""
) -> List[str]:
    """Generates a list of all possible labels for a given IRI or BNode.
    This list is used for the visualisation of the resource in the LOD view.
    :param lang: the language preference for the labels.
    """
    my_literal_list = (
        [Literal(label) for label in rdf_graph.objects(node, SKOS.prefLabel)]
        + [Literal(name) for name in rdf_graph.objects(node, SDO.name)]
        + [Literal(name) for name in rdf_graph.objects(node, SDO.alternativeHeadline)]
        + [Literal(title) for title in rdf_graph.objects(node, DCTERMS.title)]
        + [Literal(label) for label in rdf_graph.objects(node, RDFS.label)]
        + [
            Literal(lf)
            for lf in rdf_graph.objects(node, URIRef(f"{SKOSXL}literalForm"))
        ]
    )
    my_literal_list = sorted(
        my_literal_list,
        key=lambda lit: (
            0 if lit.language == lang else 1
        ),  # preferred language first, then the rest
    )
    return [get_string_for_langstring(label, lang) for label in my_literal_list]


def get_string_for_langstring(literal: Literal, lang: str = "") -> str:
    """Returns the string value of a Literal, taking into account the
    language preference. If the literal has a language tag that matches
    the preferred language, the string value is returned without the language
    tag. If the literal has a language tag that does not match the preferred
    language, the string value is returned with the language tag. For other
    cases (e.g. no language tag defined), the string value is returned without
    the language tag.
    :param lang: the language preference for the labels.
    """
    if literal.language is None:
        # no language tag defined: return the string value
        return str(literal)
    elif literal.language and lang == "":
        # no preferred language defined but language tag defined:
        # return the string value including language tag, to make it clear that
        # there is a language tag defined
        return f"{str(literal)} @{literal.language}"
    elif literal.language and lang != "" and literal.language == lang:
        # language tag defined, there is a preferred language and it matches the
        # literal's language: return the string value (because the UI is all
        # in that preferred language, no need to add the language tag)
        return str(literal)
    elif literal.language and literal.language != lang:
        # language tag defined but does not match the preferred language:
        # return the string value with the language tag
        return f"{str(literal)} @{literal.language}"
    else:
        # this should not happen, but in case it does, return the empty string
        return ""


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
    """Generates a list of labels for a given Literal, taking language
    preference into account.
    :param lang: the language preference for the labels.
    """
    return {"labels": [get_string_for_langstring(literal, lang)]}
    # | json_for_datatype(literal.graph, literal.datatype)


def json_header_from_rdf_graph(
    rdf_graph: Graph, resource_url: str
) -> Optional[List[dict]]:
    """Generates the JSON data for the header in lodview."""
    json_header = []
    try:
        json_header = [
            {
                "title": json_label_for_node(
                    rdf_graph,
                    URIRef(resource_url),
                    lang=cfg.get("UI_LANGUAGE_PREFERENCE", "nl"),
                ),
                "o": [
                    json_parts_from_IRI(rdf_graph, str(o))
                    for o in rdf_graph.objects(
                        subject=URIRef(resource_url), predicate=URIRef(RDF.type)
                    )
                    if json_parts_from_IRI(rdf_graph, str(o)).get("namespace", "")
                    in (
                        str(SDO),
                        str(SKOS),
                        str(SCHEMA),
                        str(MUZIEKWEB_VOCAB),
                        str(OWL),
                    )
                ],
            }
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
                | {
                    "labels": json_label_for_node(
                        rdf_graph, o, lang=cfg.get("UI_LANGUAGE_PREFERENCE", "nl")
                    )
                },
            }
            for (p, o) in rdf_graph.predicate_objects(subject=URIRef(resource_url))
            if isinstance(o, URIRef)
        ]
        return json_iri_iri
    except Exception as e:
        logger.exception(f"Error in json_iri_iri_from_rdf_graph: {str(e)}")
        logger.error(json_iri_iri)
    return json_iri_iri


def json_iri_lit_from_rdf_graph(rdf_graph: Graph, resource_url: str) -> List[dict]:
    """Generates JSON structured data (<uri> <uri> literal) to be used in the LOD view templates."""
    json_iri_lit = []
    try:
        json_iri_lit = [
            {
                "p": json_parts_from_IRI(rdf_graph, str(p)),
                "o": (
                    json_label_for_literal(
                        o,
                        lang=cfg.get("UI_LANGUAGE_PREFERENCE", "nl"),
                    )
                    if o.datatype is None
                    else json_label_for_literal(
                        o, lang=cfg.get("UI_LANGUAGE_PREFERENCE", "nl")
                    )
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
    json_iri_bnode = []
    try:
        for p, o in rdf_graph.predicate_objects(subject=URIRef(resource_url)):
            if p != RDF.type and isinstance(o, BNode):
                bnode_content = [
                    {
                        "pred": json_parts_from_IRI(rdf_graph, str(bnode_pred)),
                        "obj": (
                            json_parts_from_IRI(rdf_graph, str(bnode_obj))
                            | {
                                "labels": json_label_for_node(
                                    rdf_graph,
                                    bnode_obj,
                                    lang=cfg.get("UI_LANGUAGE_PREFERENCE", "nl"),
                                )
                            }
                            if isinstance(bnode_obj, URIRef)
                            else (
                                json_for_literal(
                                    rdf_graph,
                                    bnode_obj,
                                    lang=cfg.get("UI_LANGUAGE_PREFERENCE", "nl"),
                                )
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


def json_inverse_relations_for_resource(
    resource_url: str, sparql_endpoint: str
) -> list:
    """Query the sparql endpoint for inverse relations and create a JSON structure
    that is used in the lod view inverse relations."""
    if util.ld_util.ask_for_inverse_relations(resource_url, sparql_endpoint):
        g = util.ld_util.get_inverse_relations_from_rdf_store(
            resource_url, sparql_endpoint
        )

        # Count occurrences of each predicate (property) for a given resource URI.
        property_counts = Counter(p for p in g.predicates(None, URIRef(resource_url)))
        if logger.getEffectiveLevel() == logging.DEBUG:
            for prop, count in property_counts.items():
                logger.debug(f"{prop}: {count}")

        return [
            {
                "p": json_parts_from_IRI(g, str(property)),
                "count": count,
                "resources": [
                    {
                        "s": json_parts_from_IRI(g, str(s))
                        | {
                            "labels": json_label_for_node(
                                g,
                                s,
                                lang=cfg.get("UI_LANGUAGE_PREFERENCE", "nl"),
                            )
                        }
                    }
                    for s in itertools.islice(
                        g.subjects(property, URIRef(resource_url), unique=True), 0, 100
                    )
                    if isinstance(s, URIRef)
                ],
            }
            for property, count in property_counts.items()
        ]
    return []


def generate_html_page(
    rdf_graph: Graph,
    resource_iri: str,
    sparql_endpoint: str,
    template: str = "bg_resource.html",
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
    html_template: str = "bg_resource.html",
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
            json_inverse_relations=json_inverse_relations_for_resource(
                resource_url, sparql_endpoint
            ),
            sparql_endpoint=sparql_endpoint,
            album_art=util.ld_util.get_album_art_from_rdf_graph(
                rdf_graph, resource_url
            ),
            pref_language=cfg.get("UI_LANGUAGE_PREFERENCE", "nl").upper(),
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
        "lod_view_header.html",
        resource_uri=resource_uri,
        rdf_graph_header_json=rdf_graph_header_json,
    )
