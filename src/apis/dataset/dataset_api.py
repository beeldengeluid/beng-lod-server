import logging
from flask import current_app, request, render_template, Response
from flask_restx import Namespace, Resource
from apis.dataset.DataCatalogLODHandler import DataCatalogLODHandler
from util.mime_type_util import MimeType
from models.DatasetApiUriLevel import DatasetApiUriLevel
import util.ld_util
from util.APIUtil import APIUtil


logger = logging.getLogger()


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
        logger.info(f"Getting RDF for resource {resource_url} from triple store.")
        rdf_graph = util.ld_util.get_lod_resource_from_rdf_store(
            resource_url, sparql_endpoint, nisv_organisation_uri
        )
        if rdf_graph is not None:
            logger.info(f"Generating HTML page for {resource_url}.")
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

    @api.produces([mt.value for mt in MimeType])
    def get(self, number=None):
        """Get the RDF for the Dataset, including its DataDownloads.
        All triples for the Dataset and its DataDownloads are included.
        """
        dataset_uri = util.ld_util.generate_lod_resource_uri(
            DatasetApiUriLevel.DATASET, number, current_app.config["BENG_DATA_DOMAIN"]
        )
        # check if resource exists
        if self.is_dataset(dataset_uri) is False:
            logger.error(f"Dataset doesn't exist: {dataset_uri}.")
            return APIUtil.toErrorResponse("not_found")

        # check if dataset is valid
        if self.is_valid_dataset(dataset_uri) is False:
            logger.error(f"Dataset is not valid: {dataset_uri}.")
            return APIUtil.toErrorResponse("bad_request", "Invalid Dataset")

        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = (
            MimeType.JSON_LD
        )  # we choose to set a default if the user has not specified
        if best_match is not None:
            mime_type = MimeType(best_match)

        if mime_type is MimeType.HTML:
            # note that data for HTML are delivered from the RDF store
            logger.info(f"Generating HTML page for {dataset_uri}.")
            html_page = self._get_lod_view_resource(
                dataset_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return Response(html_page, mimetype=mime_type.value)
            else:
                logger.error(f"Could not generate the HTML page for {dataset_uri}.")
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        # other content formats
        logger.info(f"Get the serialization for dataset {dataset_uri}.")
        res_string = DataCatalogLODHandler(current_app.config).get_dataset(
            dataset_uri, mime_format=mime_type.to_ld_format()
        )
        if res_string:
            return Response(res_string, mimetype=mime_type.value)
        logger.error(f"Could not fetch the serialization for dataset {dataset_uri}.")
        return APIUtil.toErrorResponse("bad_request", "Invalid URI or return format")

    def is_dataset(self, dataset_uri: str) -> bool:
        return DataCatalogLODHandler(current_app.config).is_dataset(dataset_uri)

    def is_valid_dataset(self, dataset_uri: str) -> bool:
        return DataCatalogLODHandler(current_app.config).is_valid_dataset(dataset_uri)


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
    """Serve the RDF for the data catalog in the format that was requested. A data catalog contains datasets."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, number=None):
        """Get the RDF for the DataCatalog, including its Datasets.
        All triples describing the DataCatalog and its Datasets are included.
        """
        data_catalog_uri = util.ld_util.generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            number,
            current_app.config["BENG_DATA_DOMAIN"],
        )

        # check if resource exists
        if self.is_data_catalog(data_catalog_uri) is False:
            logger.error(f"The data catalog doesn't exist: {data_catalog_uri}.")
            return APIUtil.toErrorResponse("not_found")

        # check if data catalog is valid
        if self.is_valid_data_catalog(data_catalog_uri) is False:
            logger.error(f"The data catalog is invalid: {data_catalog_uri}.")
            return APIUtil.toErrorResponse("bad_request", "Invalid DataCatalog")

        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = (
            MimeType.JSON_LD
        )  # we choose to set a default if the user has not specified
        if best_match is not None:
            mime_type = MimeType(best_match)

        if mime_type is MimeType.HTML:
            # note that data for HTML are delivered from the RDF store
            logger.info(f"Generating HTML page for data catalog: {data_catalog_uri}.")
            html_page = self._get_lod_view_resource(
                data_catalog_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return Response(html_page, mimetype=mime_type.value)
            else:
                logger.error(
                    f"Could not generate proper HTML page for data catalog: {data_catalog_uri}."
                )
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        # other mime types
        logger.info(
            f"Getting the RDF in proper serialization format for data catalog: {data_catalog_uri}."
        )
        res_string = DataCatalogLODHandler(current_app.config).get_data_catalog(
            data_catalog_uri, mime_format=mime_type.to_ld_format()
        )
        if res_string:
            return Response(res_string, mimetype=mime_type.value)
        logger.error(
            f"Error in fetching the serialization for data catalog: {data_catalog_uri}."
        )
        return APIUtil.toErrorResponse("bad_request", "Invalid URI or return format")

    def is_data_catalog(self, data_catalog_uri: str) -> bool:
        return DataCatalogLODHandler(current_app.config).is_data_catalog(
            data_catalog_uri
        )

    def is_valid_data_catalog(self, data_catalog_uri: str) -> bool:
        return DataCatalogLODHandler(current_app.config).is_valid_data_catalog(
            data_catalog_uri
        )


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
    """Serve the RDF for the data downloads in the format that was requested."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, number=None):
        """Get the RDF for the DataDownload."""
        data_download_uri = util.ld_util.generate_lod_resource_uri(
            DatasetApiUriLevel.DATADOWNLOAD,
            number,
            current_app.config["BENG_DATA_DOMAIN"],
        )
        if self.is_data_download(data_download_uri) is False:
            logger.error(f"Data download does not exist: {data_download_uri}")
            return APIUtil.toErrorResponse("not_found")

        if not self.is_valid_data_download(data_download_uri):
            logger.error(f"Invalid data download: {data_download_uri}")
            return APIUtil.toErrorResponse("bad_request", "Invalid DataDownload")

        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = (
            MimeType.JSON_LD
        )  # we choose to set a default if the user has not specified
        if best_match is not None:
            mime_type = MimeType(best_match)

        if mime_type is MimeType.HTML:
            # note that data for HTML are delivered from the RDF store
            logger.info(f"Generating HTML page for data download: {data_download_uri}.")
            html_page = self._get_lod_view_resource(
                data_download_uri,
                current_app.config.get("SPARQL_ENDPOINT"),
                current_app.config.get("URI_NISV_ORGANISATION"),
            )
            if html_page:
                return Response(html_page, mimetype=mime_type.value)
            else:
                logger.error(
                    f"Could not generate HTML page for data download: {data_download_uri}."
                )
                return APIUtil.toErrorResponse(
                    "internal_server_error",
                    "Could not generate an HTML view for this resource",
                )

        # other return formats
        logger.info(
            f"Getting the RDF in proper serialization format for data download: {data_download_uri}."
        )
        res_string = DataCatalogLODHandler(current_app.config).get_data_download(
            data_download_uri, mime_format=mime_type.to_ld_format()
        )
        if res_string:
            return Response(res_string, mimetype=mime_type.value)
        logger.error(
            f"Error in fetching the serialization for data download: {data_download_uri}."
        )
        return APIUtil.toErrorResponse("bad_request", "Invalid URI or return format")

    def is_data_download(self, data_download_uri: str) -> bool:
        return DataCatalogLODHandler(current_app.config).is_data_download(
            data_download_uri
        )

    def is_valid_data_download(self, data_download_uri: str) -> bool:
        return DataCatalogLODHandler(current_app.config).is_valid_data_download(
            data_download_uri
        )
