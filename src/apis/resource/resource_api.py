import logging

from flask import current_app, request, Response, render_template
from flask_restx import Namespace, Resource

import util.ld_util

from models.ResourceApiUriLevel import ResourceApiUriLevel
from util.APIUtil import APIUtil
from util.mime_type_util import MimeType

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
        500: "Server error",
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
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = MimeType.JSON_LD
        if best_match is not None:
            mime_type = MimeType(best_match)

        lod_url = None
        try:
            lod_url = util.ld_util.generate_lod_resource_uri(
                ResourceApiUriLevel(cat_type),
                identifier,
                current_app.config.get("BENG_DATA_DOMAIN"),
            )
        except ValueError:
            logger.error(
                "Could not generate LOD resource URI. Invalid resource level supplied."
            )
            return APIUtil.toErrorResponse(
                "bad_request", "Invalid resource level supplied"
            )
        except Exception:
            print("test")

        if mime_type is MimeType.HTML:
            logger.info(f"Generating HTML page for {lod_url}.")
            html_page = self._get_lod_view_resource(
                lod_url,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return Response(html_page, mimetype=mime_type.value)
            else:
                logger.error(
                    f"Could not generate an HTML view for {lod_url}.",
                )
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource.",
                )

        logger.info(
            f"Getting the RDF in the proper serialization format for {lod_url}."
        )
        rdf_graph = util.ld_util.get_lod_resource_from_rdf_store(
            lod_url,
            current_app.config.get("SPARQL_ENDPOINT"),
            current_app.config.get("URI_NISV_ORGANISATION"),
        )
        if rdf_graph is not None:
            serialised_graph = rdf_graph.serialize(
                format=mime_type.to_ld_format(), auto_compact=True
            )
            if serialised_graph:
                return Response(serialised_graph, mimetype=mime_type.value)
            else:
                return APIUtil.toErrorResponse(
                    "internal_server_error", "Serialisation failed"
                )
        else:
            return APIUtil.toErrorResponse(
                "internal_server_error",
                "No graph created. Check your resource type and identifier",
            )

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
        rdf_graph = util.ld_util.get_lod_resource_from_rdf_store(
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
                structured_data=util.ld_util.json_ld_structured_data_for_resource(
                    rdf_graph, resource_url
                ),
                json_header=util.ld_util.json_header_from_rdf_graph(
                    rdf_graph, resource_url
                ),
                json_iri_iri=util.ld_util.json_iri_iri_from_rdf_graph(
                    rdf_graph, resource_url
                ),
                json_iri_lit=util.ld_util.json_iri_lit_from_rdf_graph(
                    rdf_graph, resource_url
                ),
                json_iri_bnode=util.ld_util.json_iri_bnode_from_rdf_graph(
                    rdf_graph, resource_url
                ),
                nisv_sparql_endpoint=sparql_endpoint,
            )
        logger.error(
            f"Triple data for lod view could not be retrieved from the triple store for {resource_url}."
        )
        return None
