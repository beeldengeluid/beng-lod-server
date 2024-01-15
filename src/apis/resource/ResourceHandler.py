import logging
from flask import Response, render_template

import util.ld_util as ld_util

from models.ResourceURILevel import ResourceURILevel
from util.APIUtil import APIUtil
from util.mime_type_util import MimeType

logger = logging.getLogger()

class ResourceHandler():
    @staticmethod
    def get_lod_for_resource_in_type(mime_type: MimeType, identifier: str, data_domain: str, sparql_endpoint: str, nisv_organisation: str, cat_type="program"):
        lod_url = None
        try:
            lod_url = ld_util.generate_lod_resource_uri(
                ResourceURILevel(cat_type),
                identifier,
                data_domain,
            )
        except ValueError:
            logger.error(
                "Could not generate LOD resource URI. Invalid resource level supplied."
            )
            return APIUtil.toErrorResponse(
                "bad_request", "Invalid resource level supplied"
            )

        if mime_type is MimeType.HTML:
            # note that data for HTML is requested from the RDF store, so no need to do is_public_resource
            logger.info(f"Generating HTML page for {lod_url}.")
            html_page = ResourceHandler._get_lod_view_resource(
                lod_url,
                sparql_endpoint,
                nisv_organisation,
            )
            if html_page:
                return APIUtil.toSuccessResponse(html_page)
            else:
                logger.error(
                    f"Could not generate an HTML view for {lod_url}.",
                )
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource.",
                )

        if mime_type:
            # note we need to use empty params for the UI
            logger.info(
                f"Getting the RDF in the proper serialization format for {lod_url}."
            )
            rdf_graph = ld_util.get_lod_resource_from_rdf_store(
            lod_url, 
            sparql_endpoint,
                nisv_organisation
            )
            if rdf_graph is not None:
                serialised_graph = rdf_graph.serialize(format=mime_type)
                if serialised_graph:
                    return APIUtil.toSuccessResponse(serialised_graph)
                else:
                    return Response("Error: serialisation failed")
            else:
                return Response("Error: no graph created")
        logger.error("Error: no mime type was given.")
        return APIUtil.toErrorResponse("bad_request", "No mime type detected...")

    @staticmethod
    def _get_lod_view_resource(
        resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str
    ):
        """Handler that, given a URI, gets RDF from the SPARQL endpoint and generates an HTML page.
        :param resource_url: The URI for the resource.
        :param sparql_endpoint - the SPARQL endpoint to get the resource from
        :param nisv_organisation_uri - the URI identifying the NISV organisation, for provenance
        """
        logger.info(
            f"Getting the graph from the triple store for resource {resource_url}."
        )
        rdf_graph = ld_util.get_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, nisv_organisation_uri
        )
        if rdf_graph:
            logger.info(
                f"A valid graph ({len(rdf_graph)} triples) was retrieved from the RDF store. "
                "Returning a rendered HTML template 'resource.html'."
            )
            return render_template(
                "resource.html",
                resource_uri=resource_url,
                structured_data=ld_util.json_ld_structured_data_for_resource(
                    rdf_graph, resource_url
                ),
                json_header=ld_util.json_header_from_rdf_graph(rdf_graph, resource_url),
                json_iri_iri=ld_util.json_iri_iri_from_rdf_graph(rdf_graph, resource_url),
                json_iri_lit=ld_util.json_iri_lit_from_rdf_graph(rdf_graph, resource_url),
                json_iri_bnode=ld_util.json_iri_bnode_from_rdf_graph(rdf_graph, resource_url),
                nisv_sparql_endpoint=sparql_endpoint,
            )
        logger.error(
            f"Triple data for lod view could not be retrieved from the triple store for {resource_url}."
        )
        return None
