import logging

from flask import current_app, request
from flask_restx import Namespace, Resource

from apis.resource.ResourceHandler import ResourceHandler
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
        500: "Server error"
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
        resource_handler = ResourceHandler
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = MimeType.JSON_LD
        if best_match is not None:
            mime_type = MimeType(best_match)

        return resource_handler.get_lod_for_resource_in_type(mime_type, 
                                                             identifier, 
                                                             current_app.config.get("BENG_DATA_DOMAIN"), 
                                                             current_app.config.get("SPARQL_ENDPOINT"), 
                                                             current_app.config.get("URI_NISV_ORGANISATION"), 
                                                             cat_type)
