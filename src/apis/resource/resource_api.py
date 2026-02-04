import logging
from flask import current_app, request, Response
from flask_restx import Namespace, Resource
import util.ld_util
import util.mw_ld_util
from models.ResourceApiUriLevel import ResourceApiUriLevel
from util.APIUtil import APIUtil
from util.mime_type_util import MimeType
import util.lodview_util
import util.mw_lodview_util

logger = logging.getLogger()


api = Namespace(
    "resource",
    description="Audiovisual catalog items in RDF.",
)


@api.doc(
    responses={
        200: "Success",
        302: "Found",
        400: "Bad request.",
        404: "Resource does not exist.",
        500: "Server error",
    }
)
@api.route(
    "id/<any(program, series, season, scene):cat_type>/<identifier>",
    endpoint="dereference",
)
class ResourceAPI(Resource):
    """Serve the RDF for the media catalog resources in the format that was requested."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, identifier, cat_type="program"):
        # determine and set the mimetype
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types, MimeType.JSON_LD.value
        )
        mime_type = MimeType(best_match)

        # create the lod_url and 302 redirect when it's a RDA postfix
        lod_url = None
        try:
            # check for _<wemi>-postfix: "_work", "_expression", "_manifestation"
            status, identifier = self.check_for_wemi_postfix(identifier)
            lod_url = util.ld_util.generate_lod_resource_uri(
                ResourceApiUriLevel(cat_type),
                identifier,
                current_app.config.get("BENG_DATA_DOMAIN", ""),
            )
            if status == 302:
                return Response(
                    None,
                    status=status,
                    headers={"location": lod_url},
                    mimetype=mime_type.value,
                )
        except ValueError:
            logger.error("Could not generate LOD resource URI.")
            return APIUtil.toErrorResponse(
                "bad_request", "Invalid catalog type or identifier supplied"
            )
        except Exception as e:
            logger.exception(
                f"Unknown error while generating lod resource uri for {ResourceApiUriLevel(cat_type)} and {identifier}."
            )
            return APIUtil.toErrorResponse("internal_server_error", e)

        # check if identifier is proper digit string, return 400 if not.
        if not identifier.isdigit():
            return APIUtil.toErrorResponse(
                "bad_request", "Invalid daan identifier supplied."
            )

        # check if resource exists and return 404 if it doesn't.
        if not util.ld_util.is_nisv_cat_resource(
            lod_url, current_app.config.get("SPARQL_ENDPOINT", "")
        ):
            return APIUtil.toErrorResponse("not_found")

        # getting and returning lod data
        logger.info(f"Getting the graph from the triple store for resource {lod_url}.")
        rdf_graph = util.ld_util.get_lod_resource_from_rdf_store(
            lod_url,
            current_app.config.get("SPARQL_ENDPOINT", ""),
            current_app.config.get("URI_NISV_ORGANISATION", ""),
        )
        # TODO: add the mw_ld_util version here and compare graphs (DEVELOPMENT ONLY)
        rdf_graph_mw = util.mw_ld_util.get_resource_from_rdf_store(
            lod_url,
            current_app.config.get("SPARQL_ENDPOINT", ""),
            current_app.config.get("MUZIEKWEB_LOD_RESOURCE_QUERY", ""),
            current_app.config.get("URI_NISV_ORGANISATION", ""),
        )
        # TODO: comparison of both graphs here (DEVELOPMENT ONLY)
        util.ld_util.compare_graphs(rdf_graph, rdf_graph_mw)

        # check if graph contains data and return 500 if not.
        if not rdf_graph:
            return APIUtil.toErrorResponse(
                "internal_server_error",
                "No graph created. Check your resource type and identifier",
            )

        # check if mime_type is HTML and generate HTML page and 200 if so.
        if mime_type is MimeType.HTML:
            # TODO: switch to mw_lodview_util when ready
            return util.mw_lodview_util.generate_html_page(
                rdf_graph, lod_url, current_app.config.get("SPARQL_ENDPOINT", "")
            )
            # return util.lodview_util.generate_html_page(
            #     rdf_graph, lod_url, current_app.config.get("SPARQL_ENDPOINT", "")
            # )
        else:
            # return other formats than HTML. Returns data and 200 status.
            return util.lodview_util.get_serialised_graph(rdf_graph, mime_type)

    def check_for_wemi_postfix(self, identifier: str) -> tuple[int, str]:
        """Try to split the identifier and detect the wemi entity postfix.
        Always returns the DAAN ID without postfix or raises ValueError when
        an unvalid postfix was found.
        :param identifier: string with the DAAN ID, incl. postfix or without.
        :returns: tuple containing 'status_code' 302 when postfix is included or 200,
        and 'identifier', always the DAAN ID without postfix."""
        status_code = 200
        identifier_list = identifier.split("_", 1)
        split_identifier = identifier_list[0]
        if len(identifier_list) == 2:
            if identifier_list[1] in (
                "work",
                "expression",
                "manifestation",
            ):
                status_code = 302
            else:
                logger.error(
                    "Identifier _WEMI postfix is not one of 'work', 'expression' or 'manifestation'."
                )
                raise ValueError
        return (status_code, split_identifier)
