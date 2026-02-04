import logging
from flask import current_app, request
from flask_restx import Namespace, Resource
from util.mime_type_util import MimeType
from util.APIUtil import APIUtil
import util.ld_util
import util.lodview_util

logger = logging.getLogger()


api = Namespace(
    "gtaa",
    description="GTAA thesaurus terms as SKOS Concepts.",
)


# noinspection PyMethodMayBeStatic
@api.doc(
    responses={
        200: "Success",
        400: "Bad request.",
        404: "Resource does not exist.",
        406: "Not Acceptable. The requested format in the Accept header is not supported by the server.",
    }
)
@api.route(
    "gtaa/<identifier>",
    endpoint="gtaa_stuff",
    doc={
        "params": {
            "identifier": "skos:notation (an integer) value for GTAA Concepts or alphanumerical value for GTAA ConceptSchemes."
        }
    },
)
class GTAAAPI(Resource):
    """Serve the RDF for the GTAA SKOS Concepts in the format that was requested."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, identifier):
        gtaa_uri = f'{current_app.config.get("BENG_DATA_DOMAIN")}gtaa/{identifier}'

        # Do ASK request to triple store. Return 404 if resource doesn't exist.
        if not util.ld_util.is_skos_resource(
            gtaa_uri, current_app.config.get("SPARQL_ENDPOINT", "")
        ):
            return APIUtil.toErrorResponse("not_found")

        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = MimeType.JSON_LD
        if best_match is not None:
            mime_type = MimeType(best_match)

        rdf_graph = util.ld_util.get_lod_resource_from_rdf_store(
            gtaa_uri,
            current_app.config.get("SPARQL_ENDPOINT", ""),
            current_app.config.get("URI_NISV_ORGANISATION", ""),
        )
        if not rdf_graph:
            logger.error(f"Could not generate LOD for resource {gtaa_uri}.")
            return APIUtil.toErrorResponse(
                "internal_server_error",
                "Could not generate LOD for this resource",
            )

        if mime_type is MimeType.HTML:
            return util.lodview_util.generate_html_page(
                rdf_graph, gtaa_uri, current_app.config.get("SPARQL_ENDPOINT", "")
            )
        else:
            # another serialisation than HTML
            return util.lodview_util.get_serialised_graph(rdf_graph, mime_type)
