import logging
from flask import current_app, request, Response, render_template, make_response
from flask_restx import Namespace, Resource
from apis.mime_type_util import MimeType, get_profile_by_uri
from util.APIUtil import APIUtil
from models.DAANRdfModel import ResourceURILevel
from util.ld_util import (
    generate_lod_resource_uri,
    is_public_resource,
    get_lod_resource_from_rdf_store,
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
        406: "Not Acceptable. The requested format in the Accept header is not supported by the server.",
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
            logger.error("Invalid resource level supplied")
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
        accept_profile = request.headers.get("Accept-Profile")

        if mime_type is MimeType.HTML:
            # note that data for HTML is requested from the RDF store, so no need to do is_public_resource
            html_page = self._get_lod_view_resource(
                lod_url,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return make_response(html_page, 200)
            else:
                logger.error(
                    "Could not generate an HTML view for this resource",
                )
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        # NOTE: in the future design we request from triples store so no basic auth is necessary
        # only registered user can access all items
        auth_user = current_app.config.get("AUTH_USER")
        auth_pass = current_app.config.get("AUTH_PASSWORD")
        auth = request.authorization
        if (
            auth is not None
            and auth.type == "basic"
            and auth.username == auth_user
            and auth.password == auth_pass
        ):
            # no restrictions, bypass the check
            logger.debug("credentials provided. no restrictions, bypass the check.")
            pass
        else:
            # NOTE: this else clause is only there so we can download as lod-importer, but nobody else can.
            logger.debug(
                "No valid credentials provided. Only public resources, available in the triple store, are returned."
            )
            if not is_public_resource(
                lod_url, current_app.config.get("SPARQL_ENDPOINT")
            ):
                return APIUtil.toErrorResponse(
                    "access_denied", "The resource can not be dereferenced."
                )

        if mime_type:
            # note we need to use empty params for the UI
            logger.debug("Returning the requested data.")
            return self._get_lod_resource(
                level=cat_type,
                identifier=identifier,
                mime_type=mime_type,
                accept_profile=accept_profile,
                app_config=current_app.config,
            )
        logger.error("Error, because no mime type was given.")
        return Response("Error: No mime type detected...")

    def _get_lod_resource(
        self, level, identifier, mime_type, accept_profile, app_config
    ):
        """ Generates the expected data based on the mime_type.
            :param level: meaning the catalogue type: 'program' (default), 'series', 'season', 'scene'.
            :param identifier: the DAAN id.
            :param mime_type: the mime_type, or serialization the resource is requested in.
            :param accept_profile: the profile (or model/schema/ontology) the data is requested in. \
                See: https://www.w3.org/TR/dx-prof-conneg/#related-http
                Example: Accept: application/ld+json; profile="http://schema.org"
            :param app_config: the application configuration
            :return: RDF data in a response object
        """
        mt = None
        try:
            mt = MimeType(mime_type)
        except ValueError:
            logger.debug(
                "Given mime type cannot be used. Fall back to default mime type."
            )
            mt = MimeType.JSON_LD

        profile = get_profile_by_uri(accept_profile, app_config)
        profile_prefix = profile["prefix"]
        logger.debug(
            f"Getting requested resource from the flex store using profile '{profile_prefix}'."
        )
        resp, status_code, headers = profile["storage_handler"](
            app_config, profile
        ).get_storage_record(level, identifier, mt.to_ld_format())
        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            logger.debug("Valid response from the flex data store.")
            headers = {"Content-Type": mt.value}
            if profile.get("uri") is not None:
                content_profile = profile.get("uri")
                headers["Content-Profile"] = content_profile
            logger.debug(
                "Return requested data in the required serialization format and profile."
            )
            return Response(resp, mimetype=mt.value, headers=headers)
        logger.debug(
            f"Something wrong with response from the flex data store: {status_code}"
        )
        return Response(resp, status_code, headers=headers)

    def _get_lod_view_resource(
        self, resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str
    ):
        """Handler that, given a URI, gets RDF from the SPARQL endpoint and generates an HTML page.
        :param resource_url: The URI for the resource.
        """
        logger.debug(
            "Getting the graph for the requested resource from the triple store."
        )
        rdf_graph = get_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, nisv_organisation_uri
        )
        if rdf_graph:
            logger.debug(
                f"A valid graph ({len(rdf_graph)} triples) was retrieved from the RDF store.",
                "Returning a rendered HTML template 'resource.html'.",
            )
            return render_template(
                "resource.html",
                resource_uri=resource_url,
                json_header=json_header_from_rdf_graph(rdf_graph, resource_url),
                json_iri_iri=json_iri_iri_from_rdf_graph(rdf_graph, resource_url),
                json_iri_lit=json_iri_lit_from_rdf_graph(rdf_graph, resource_url),
                json_iri_bnode=json_iri_bnode_from_rdf_graph(rdf_graph, resource_url),
                nisv_sparql_endpoint=sparql_endpoint,
            )
        return None
