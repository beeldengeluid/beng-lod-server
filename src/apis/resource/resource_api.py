import logging

from flask import current_app, request, Response, render_template, make_response
from flask_restx import Namespace, Resource
from util.mime_type_util import MimeType
from models.ResourceURILevel import ResourceURILevel
from util.APIUtil import APIUtil
from util.ld_util import (
    generate_lod_resource_uri,
    get_lod_resource_from_rdf_store,
    json_ld_structured_data_for_resource,
    json_header_from_rdf_graph,
    json_iri_iri_from_rdf_graph,
    json_iri_lit_from_rdf_graph,
    json_iri_bnode_from_rdf_graph,
)

logger = logging.getLogger()


api = Namespace(
    "resource",
    description="Resources in RDF for Netherlands Institute for Sound and Vision.",
)



@api.doc(
    responses={
        200: "Success",
        400: "Bad request.",
        404: "Resource does not exist.",
    }
)
@api.route(
    "id/<any(program, series, season, scene):cat_type>/<int:identifier>",
    endpoint="dereference",
)
class ResourceAPI(Resource):
    """Serve the RDF for the media catalog resources in the format that was requested."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, identifier, cat_type="program"):
        lod_url = None
        try:
            lod_url = generate_lod_resource_uri(
                ResourceURILevel(cat_type),
                identifier,
                current_app.config.get("BENG_DATA_DOMAIN"),
            )
        except ValueError:
            logger.error(
                "Could not generate LOD resource URI. Invalid resource level supplied."
            )
            return APIUtil.toErrorResponse(
                "bad request", "Invalid resource level supplied"
            )

        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = MimeType.JSON_LD
        if best_match is not None:
            mime_type = MimeType(best_match)

        if mime_type is MimeType.HTML:
            # note that data for HTML is requested from the RDF store, so no need to do is_public_resource
            logger.info(f"Generating HTML page for {lod_url}.")
            html_page = self._get_lod_view_resource(
                lod_url,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return make_response(html_page, 200)
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
            return get_lod_resource_from_rdf_store(
            lod_url, 
            current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
        logger.error("Error: no mime type was given.")
        return Response("Error: No mime type detected...")

    def _get_lod_view_resource(
        self, resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str
    ):
        """Handler that, given a URI, gets RDF from the SPARQL endpoint and generates an HTML page.
        :param resource_url: The URI for the resource.
        :param sparql_endpoint - the SPARQL endpoint to get the resource from
        :param nisv_organisation_uri - the URI identifying the NISV organisation, for provenance
        """
        logger.info(
            f"Getting the graph from the triple store for resource {resource_url}."
        )
        rdf_graph = get_lod_resource_from_rdf_store(
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
                structured_data=json_ld_structured_data_for_resource(
                    rdf_graph, resource_url
                ),
                json_header=json_header_from_rdf_graph(rdf_graph, resource_url),
                json_iri_iri=json_iri_iri_from_rdf_graph(rdf_graph, resource_url),
                json_iri_lit=json_iri_lit_from_rdf_graph(rdf_graph, resource_url),
                json_iri_bnode=json_iri_bnode_from_rdf_graph(rdf_graph, resource_url),
                nisv_sparql_endpoint=sparql_endpoint,
            )
        logger.error(
            f"Triple data for lod view could not be retrieved from the triple store for {resource_url}."
        )
        return None
