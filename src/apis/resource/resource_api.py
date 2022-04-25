# import rdflib.plugins.parsers.jsonld
from flask import current_app, request, Response, render_template, make_response
from flask_restx import Namespace, Resource
from apis.mime_type_util import parse_accept_header, MimeType, get_profile_by_uri
from urllib.parse import urlparse, urlunparse
from util.APIUtil import APIUtil
from util.ld_util import prepare_lod_resource_uri, is_public_resource, get_lod_resource_from_rdf_store, \
    json_header_from_rdf_graph, json_iri_iri_from_rdf_graph, json_iri_lit_from_rdf_graph, \
    json_iri_bnode_from_rdf_graph


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

    def get(self, identifier, cat_type="program"):

        lod_url = prepare_lod_resource_uri(
            cat_type, 
            identifier,
            current_app.config.get("BENG_DATA_DOMAIN")
        )

        # shortcut for HTML (note that these are delivered from the RDF store, so no need to do is_public_resource
        if 'html' in str(request.headers.get("Accept")):
            headers = {
                "Content-Type": 'text/html'
            }
            html_page = self._get_lod_view_resource(
                lod_url, 
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION")
            )
            return make_response(html_page, 200)
            # return Response(html_page, 200, headers=headers)
            # return APIUtil.toSuccessResponse(data=html_page, headers=headers)

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
            pass
        else:
            # NOTE: this else clause is only there so we can download as lod-importer, but nobody else can.
            if not is_public_resource(lod_url, current_app.config.get("SPARQL_ENDPOINT")):
                return APIUtil.toErrorResponse(
                    "access_denied", "The resource can not be dereferenced."
                )

        mime_type, accept_profile = parse_accept_header(request.headers.get("Accept"))
        if mime_type:
            # note we need to use empty params for the UI
            return self._get_lod_resource(
                level=cat_type,
                identifier=identifier,
                mime_type=mime_type,
                accept_profile=accept_profile,
                app_config=current_app.config,
            )
        return Response("Error: No mime type detected...")

    def _get_lod_resource(self, level, identifier, mime_type, accept_profile, app_config):
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
            mt = MimeType.JSON_LD

        profile = get_profile_by_uri(accept_profile, app_config)

        resp, status_code, headers = profile["storage_handler"](
            app_config, profile
        ).get_storage_record(level, identifier, mt.to_ld_format())
        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            content_type = mt.value
            if headers.get("Content-Type") is not None:
                content_type = headers.get("Content-Type")
            profile_param = "=".join(["profile", '"{}"'.format(profile["schema"])])
            headers["Content-Type"] = ";".join([content_type, profile_param])
            return Response(resp, mimetype=mt.value, headers=headers)
        return Response(resp, status_code, headers=headers)

    def _get_lod_view_resource(self, resource_url, sparql_endpoint, nisv_organisation_uri):
        """Handler that, given a URI, gets RDF from the SPARQL endpoint and generates an HTML page.
        :param resource_url: The URI for the resource.
        """
        try:
            rdf_graph = get_lod_resource_from_rdf_store(
                resource_url, 
                sparql_endpoint, 
                nisv_organisation_uri
            )

            return render_template("resource.html",
                resource_uri=resource_url,
                json_header=json_header_from_rdf_graph(rdf_graph, resource_url),
                json_iri_iri=json_iri_iri_from_rdf_graph(rdf_graph, resource_url),
                json_iri_lit=json_iri_lit_from_rdf_graph(rdf_graph, resource_url),
                json_iri_bnode=json_iri_bnode_from_rdf_graph(rdf_graph, resource_url),
            )
        except Exception as e:
            return str(e)
