from flask import current_app, request, Response, make_response, render_template
from flask_restx import Namespace, Resource
from apis.dataset.DataCatalogLODHandler import DataCatalogLODHandler
from apis.mime_type_util import parse_accept_header
from models.DAANRdfModel import ResourceURILevel
from util.ld_util import (
    generate_lod_resource_uri,
    get_lod_resource_from_rdf_store,
    json_header_from_rdf_graph,
    json_iri_iri_from_rdf_graph,
    json_iri_lit_from_rdf_graph,
    json_iri_bnode_from_rdf_graph,
)
from util.APIUtil import APIUtil


api = Namespace(
    "dataset",
    description="Datasets in RDF for Netherlands Institute for Sound and Vision.",
)


class LODDataAPI(Resource):
    """Class that implements the shared (core) functionality for the data catalog."""

    def _get_lod_view_resource(
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
                json_header=json_header_from_rdf_graph(rdf_graph, resource_url),
                json_iri_iri=json_iri_iri_from_rdf_graph(rdf_graph, resource_url),
                json_iri_lit=json_iri_lit_from_rdf_graph(rdf_graph, resource_url),
                json_iri_bnode=json_iri_bnode_from_rdf_graph(rdf_graph, resource_url),
                nisv_sparql_endpoint=sparql_endpoint,
            )
        return None


@api.doc(
    responses={
        200: "Success",
        400: "Bad request.",
        404: "Resource does not exist.",
        406: "Not Acceptable. The requested format in the Accept header is not supported by the server.",
    }
)
@api.route("id/dataset/<number>", endpoint="datasets")
@api.doc(
    params={
        "number": {
            "description": "Enter a zero padded 4 digit integer value.",
            "in": "number",
        }
    }
)
class LODDatasetAPI(LODDataAPI):
    """Serve the RDF for the dataset in the format that was requested. A dataset contains distributions."""

    @api.response(404, "Resource does not exist error")
    def get(self, number=None):
        """Get the RDF for the Dataset, including its DataDownloads.
        All triples for the Dataset and its DataDownloads are included.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get("Accept"))
        dataset_uri = generate_lod_resource_uri(
            ResourceURILevel.DATASET, number, current_app.config["BENG_DATA_DOMAIN"]
        )

        # shortcut for HTML (note that these are delivered from the RDF store)
        if "html" in str(request.headers.get("Accept")):
            html_page = self._get_lod_view_resource(
                dataset_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return make_response(html_page, 200)
            else:
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        # other content
        resp, status_code, headers = DataCatalogLODHandler(
            current_app.config
        ).get_dataset(dataset_uri, mime_format=mime_type.to_ld_format())

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type.value, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


@api.doc(
    responses={
        200: "Success",
        400: "Bad request.",
        404: "Resource does not exist.",
        406: "Not Acceptable. The requested format in the Accept header is not supported by the server.",
    }
)
@api.route("id/datacatalog/<number>", endpoint="data_catalogs")
@api.doc(
    params={
        "number": {
            "description": "Enter a zero padded 4 digit integer value.",
            "in": "number",
        }
    }
)
class LODDataCatalogAPI(LODDataAPI):
    @api.response(404, "Resource does not exist error")
    def get(self, number=None):
        """Get the RDF for the DataCatalog, including its Datasets.
        All triples describing the DataCatalog and its Datasets are included.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get("Accept"))
        data_catalog_uri = generate_lod_resource_uri(
            ResourceURILevel.DATACATALOG,
            number,
            current_app.config["BENG_DATA_DOMAIN"],
        )

        mime_type, accept_profile = parse_accept_header(request.headers.get("Accept"))
        if mime_type is MimeType.HTML:
            # note that data for HTML are delivered from the RDF store
            html_page = self._get_lod_view_resource(
                data_catalog_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return make_response(html_page, 200)
            else:
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        # other content
        resp, status_code, headers = DataCatalogLODHandler(
            current_app.config
        ).get_data_catalog(data_catalog_uri, mime_format=mime_type.to_ld_format())

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type.value, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


@api.doc(
    responses={
        200: "Success",
        400: "Bad request.",
        404: "Resource does not exist.",
        406: "Not Acceptable. The requested format in the Accept header is not supported by the server.",
    }
)
@api.route("id/datadownload/<number>", endpoint="data_downloads")
@api.doc(
    params={
        "number": {
            "description": "Enter a zero padded 4 digit integer value.",
            "in": "number",
        }
    }
)
class LODDataDownloadAPI(LODDataAPI):
    @api.response(404, "Resource does not exist error")
    def get(self, number=None):
        """Get the RDF for the DataDownload."""
        mime_type, accept_profile = parse_accept_header(request.headers.get("Accept"))
        data_download_uri = generate_lod_resource_uri(
            ResourceURILevel.DATADOWNLOAD,
            number,
            current_app.config["BENG_DATA_DOMAIN"],
        )

        # shortcut for HTML (note that these are delivered from the RDF store)
        if "html" in str(request.headers.get("Accept")):
            html_page = self._get_lod_view_resource(
                data_download_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return make_response(html_page, 200)
            else:
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        resp, status_code, headers = DataCatalogLODHandler(
            current_app.config
        ).get_data_download(data_download_uri, mime_format=mime_type.to_ld_format())

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type.value, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers
