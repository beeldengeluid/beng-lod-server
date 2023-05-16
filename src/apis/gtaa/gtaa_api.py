import logging
from flask import current_app, request, Response, render_template, make_response
from flask_restx import Namespace, Resource
from apis.mime_type_util import MimeType
from util.APIUtil import APIUtil
from util.ld_util import (
    get_lod_resource_from_rdf_store,
    json_ld_structured_data_for_resource,
    json_header_from_rdf_graph,
    json_iri_iri_from_rdf_graph,
    json_iri_lit_from_rdf_graph,
    json_iri_bnode_from_rdf_graph,
)


logger = logging.getLogger()


api = Namespace(
    "gtaa",
    description="Thesaurus resources coming from the GTAA in RDF for Netherlands Institute for Sound and Vision.",
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
)
class GTAAAPI(Resource):
    """Serve the RDF for the GTAA SKOS Concepts in the format that was requested."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, identifier):
        gtaa_uri = f'{current_app.config.get("BENG_DATA_DOMAIN")}gtaa/{identifier}'
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = MimeType.JSON_LD
        if best_match is not None:
            mime_type = MimeType(best_match)

        if mime_type is MimeType.HTML:
            logger.info(f"Generating HTML page for resource {gtaa_uri}.")
            html_page = self._get_lod_view_gtaa(
                gtaa_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return make_response(html_page, 200)
            else:
                logger.error(f"Could not generate HTML page for resource {gtaa_uri}.")
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        if mime_type:
            # note we need to use empty params for the UI
            logger.info(
                f"Getting the RDF in proper serialization format for GTAA resource: {gtaa_uri}."
            )
            return self._get_lod_gtaa(
                gtaa_uri,
                mime_type,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
        logger.error("Not a proper mime type in the request.")
        return Response("Error: No mime type detected...")

    def _get_lod_gtaa(
        self,
        gtaa_uri: str,
        mime_type: MimeType,
        sparql_endpoint: str,
        nisv_organisation_uri: str,
    ):
        """Generates the expected data based on the mime_type.
        :param gtaa_uri: the GTAA id.
        :param mime_type: the mime_type, or serialization the resource is requested in.
        :param sparql_endpoint: endpoint URL
        :param nisv_organisation_uri: URI for the publisher
        :return: RDF data in a response object
        """
        mt_ld_format = mime_type.to_ld_format()
        ld_type = mt_ld_format if mt_ld_format is not None else "json-ld"

        rdf_graph = get_lod_resource_from_rdf_store(
            gtaa_uri, sparql_endpoint, nisv_organisation_uri
        )
        if rdf_graph:
            # serialize using the mime_type
            resp = rdf_graph.serialize(format=ld_type)
            headers = {"Content-Type": mime_type.value}
            return Response(resp, mimetype=mime_type.value, headers=headers)
        logger.error(
            f"Could not get the data for GTAA resource {gtaa_uri} from triple store at {sparql_endpoint}."
        )
        return None

    def _get_lod_view_gtaa(
        self, resource_url: str, sparql_endpoint: str, nisv_organisation_uri: str
    ):
        """Handler that, given a URI, gets RDF from the SPARQL endpoint and generates an HTML page.
        :param resource_url: The URI for the resource.
        """
        rdf_graph = get_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, nisv_organisation_uri
        )
        if rdf_graph:
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
            f"Could not get the data for GTAA resource {resource_url} from triple store at {sparql_endpoint}."
        )
        return None
