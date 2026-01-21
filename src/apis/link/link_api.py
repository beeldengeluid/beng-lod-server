import logging
from flask import request, current_app  # , Response
from flask_restx import Namespace, Resource
from util.mime_type_util import MimeType
from util.APIUtil import APIUtil
import util.lodview_util
import util.mw_ld_util

logger = logging.getLogger()

api = Namespace("Link", description="Endpoint for the Muziekweb resources.")


@api.doc(
    responses={
        200: "Success",
        302: "Found",
        400: "Bad request.",
        404: "Resource does not exist.",
        500: "Server error",
    }
)
@api.route("Link/<identifier>", endpoint="muziekweb")
class Link(Resource):
    @api.produces([mt.value for mt in MimeType])
    def get(self, identifier):
        # determine and set the mimetype
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types, MimeType.JSON_LD.value
        )
        mime_type = MimeType(best_match)

        lod_url = None
        try:
            lod_url = util.mw_ld_util.generate_muziekweb_lod_resource_uri(
                identifier,
                current_app.config.get("MUZIEKWEB_DATA_DOMAIN", ""),
            )
        except ValueError:
            logger.error("Could not generate LOD resource URI.")
            return APIUtil.toErrorResponse("bad_request", "Invalid identifier supplied")
        except Exception as e:
            logger.exception(
                f"Unknown error while generating lod resource uri for {identifier}."
            )
            return APIUtil.toErrorResponse("internal_server_error", e)

        # check if identifier is proper digit string, return 400 if not.
        if not identifier.isalnum():
            return APIUtil.toErrorResponse(
                "bad_request", "Invalid daan identifier supplied."
            )

        # check if resource exists and return 404 if it doesn't.
        if not util.mw_ld_util.is_muziekweb_resource(
            lod_url, current_app.config.get("MUZIEKWEB_SPARQL_ENDPOINT", "")
        ):
            return APIUtil.toErrorResponse("not_found")

        # getting and returning lod data
        logger.info(f"Getting the graph from the triple store for resource {lod_url}.")
        rdf_graph = util.mw_ld_util.get_resource_from_rdf_store(
            lod_url,
            current_app.config.get("MUZIEKWEB_SPARQL_ENDPOINT", ""),
            current_app.config.get("MUZIEKWEB_LOD_RESOURCE_QUERY", ""),
            current_app.config.get("MUZIEKWEB_ORGANISATION_URI", ""),
        )
        # check if graph contains data and return 500 if not.
        if not rdf_graph:
            return APIUtil.toErrorResponse(
                "internal_server_error",
                "No graph created. Check your identifier",
            )

        # check if mime_type is HTML and generate HTML page and 200 if so.
        if mime_type is MimeType.HTML:
            logger.debug("Generating HTML page.")
            muziekweb_html_template = current_app.config.get(
                "MUZIEKWEB_HTML_TEMPLATE", ""
            )
            return util.lodview_util.generate_html_page(
                rdf_graph,
                lod_url,
                current_app.config.get("MUZIEKWEB_SPARQL_ENDPOINT", ""),
                muziekweb_html_template,
            )
        else:
            # return other formats than HTML. Returns data and 200 status.
            return util.lodview_util.get_serialised_graph(rdf_graph, mime_type)
