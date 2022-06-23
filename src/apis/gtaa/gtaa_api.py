from flask import current_app, request, Response, render_template, make_response
from flask_restx import Namespace, Resource
from apis.mime_type_util import MimeType
from util.APIUtil import APIUtil
from util.ld_util import (
    get_lod_resource_from_rdf_store,
    json_header_from_rdf_graph,
    json_iri_iri_from_rdf_graph,
    json_iri_lit_from_rdf_graph,
    json_iri_bnode_from_rdf_graph,
)

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
    def get(self, identifier):

        gtaa_uri = f'{current_app.config.get("BENG_DATA_DOMAIN")}gtaa/{identifier}'

        # TODO: add the parameter 'format' so that a return format can also be added as parameter to the URL,
        # instead of only allowing content negotiation by the accept http header. The rationale is that we
        # can't send a request from the lod-view with an accept header. It just isn't possible.
        # The should not be shown when the json-ld, etc. formatted data is shown in the browser. It should list the
        # resource URI only. Still a coolURI
        # NOTE that we can also add LD in the script tag. Perhaps, using something like Comunica client, we can
        # load the data in JS, and serialize the graph in the requested format. In that case we don't
        # even need to add a parameter to the server.

        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = MimeType.JSON_LD
        if best_match is not None:
            mime_type = MimeType(best_match)

        if mime_type is MimeType.HTML:
            html_page = self._get_lod_view_gtaa(
                gtaa_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
                current_app.config.get("NAMED_GRAPH_THESAURUS"),
            )
            if html_page:
                return make_response(html_page, 200)
            else:
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        if mime_type:
            # note we need to use empty params for the UI
            return self._get_lod_gtaa(
                gtaa_uri,
                mime_type,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
                current_app.config.get("NAMED_GRAPH_THESAURUS"),
            )
        return Response("Error: No mime type detected...")

    def _get_lod_gtaa(
        self,
        gtaa_uri: str,
        mime_type: MimeType,
        sparql_endpoint: str,
        nisv_organisation_uri: str,
        thesaurus_named_graph: str,
    ):
        """Generates the expected data based on the mime_type.
        :param gtaa_uri: the GTAA id.
        :param mime_type: the mime_type, or serialization the resource is requested in.
        :param sparql_endpoint: endpoint URL
        :param nisv_organisation_uri: URI for the publisher
        :param thesaurus_named_graph: named grpah in the RDF store containing the GTAA triples
        :return: RDF data in a response object
        """
        mt_ld_format = mime_type.to_ld_format()
        ld_type = mt_ld_format if mt_ld_format is not None else "json-ld"

        rdf_graph = get_lod_resource_from_rdf_store(
            gtaa_uri,
            sparql_endpoint,
            nisv_organisation_uri,
            named_graph=thesaurus_named_graph,
        )
        if rdf_graph:
            # serialize using the mime_type
            resp = rdf_graph.serialize(format=ld_type)
            headers = {"Content-Type": mime_type.value}
            return Response(resp, mimetype=mime_type.value, headers=headers)
        return None

    def _get_lod_view_gtaa(
        self,
        resource_url: str,
        sparql_endpoint: str,
        nisv_organisation_uri: str,
        thesaurus_named_graph: str,
    ):
        """Handler that, given a URI, gets RDF from the SPARQL endpoint and generates an HTML page.
        :param resource_url: The URI for the resource.
        """
        rdf_graph = get_lod_resource_from_rdf_store(
            resource_url,
            sparql_endpoint,
            nisv_organisation_uri,
            named_graph=thesaurus_named_graph,
        )
        if rdf_graph:
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
