import logging
from flask import current_app, request
from flask_restx import Namespace, Resource
from rdflib import Graph
from apis.dataset.DataCatalogLODHandler import DataCatalogLODHandler
from util.mime_type_util import MimeType
from models.DatasetApiUriLevel import DatasetApiUriLevel
from util.APIUtil import APIUtil
import util.ld_util
from util.lodview_util import generate_html_page, get_serialised_graph

logger = logging.getLogger()


api = Namespace(
    "dataset",
    description="Audiovisual open datasets (collections) in RDF.",
)


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
class LODDatasetAPI(Resource):
    """Serve the RDF for the dataset in the format that was requested. A dataset contains distributions."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, number: str = ""):
        """Get the RDF for the Dataset, including its DataDownloads.
        All triples for the Dataset and its DataDownloads are included.
        """
        # check if number is an integer value
        if not number.isdigit():
            return APIUtil.toErrorResponse(
                "bad_request", f"Invalid identifier supplied: {number}"
            )
        # generate B&G dataset IRI
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

        # determine mime_type
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = (
            MimeType.JSON_LD
        )  # we choose to set a default if the user has not specified
        if best_match is not None:
            mime_type = MimeType(best_match)

        # get rdf
        logger.info(f"Getting RDF for resource {dataset_uri} from triple store.")
        rdf_graph = Graph()
        ds_data = DataCatalogLODHandler().get_dataset(
            dataset_uri, MimeType.TURTLE.value
        )
        rdf_graph.parse(data=ds_data, format=MimeType.TURTLE.value)
        if not rdf_graph:
            return APIUtil.toErrorResponse(
                "internal_server_error",
                f"No graph created. Check resource type and identifier for {dataset_uri}",
            )
        # generate and return response
        if mime_type is MimeType.HTML:
            return generate_html_page(
                rdf_graph, dataset_uri, current_app.config.get("SPARQL_ENDPOINT", "")
            )
        else:
            # another serialisation than HTML
            return get_serialised_graph(rdf_graph, mime_type)

    def is_dataset(self, dataset_uri: str) -> bool:
        return DataCatalogLODHandler().is_dataset(dataset_uri)

    def is_valid_dataset(self, dataset_uri: str) -> bool:
        return DataCatalogLODHandler().is_valid_dataset(dataset_uri)


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
class LODDataCatalogAPI(Resource):
    """Serve the RDF for the data catalog in the format that was requested. A data catalog contains datasets."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, number: str = ""):
        """Get the RDF for the DataCatalog, including its Datasets.
        All triples describing the DataCatalog and its Datasets are included.
        """
        # check if number is an integer value
        if not number.isdigit():
            return APIUtil.toErrorResponse(
                "bad_request", f"Invalid identifier supplied: {number}"
            )
        # get B&G lod resource iri
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

        # get the mime_type
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = (
            MimeType.JSON_LD
        )  # we choose to set a default if the user has not specified
        if best_match is not None:
            mime_type = MimeType(best_match)

        # get rdf
        logger.info(f"Getting RDF for resource {data_catalog_uri} from triple store.")
        rdf_graph = Graph()
        dc_data = DataCatalogLODHandler().get_data_catalog(
            data_catalog_uri, MimeType.TURTLE.value
        )
        rdf_graph.parse(data=dc_data, format=MimeType.TURTLE.value)
        if not rdf_graph:
            return APIUtil.toErrorResponse(
                "internal_server_error",
                f"No graph created. Check resource type and identifier for {data_catalog_uri}",
            )
        # generate and return response
        if mime_type is MimeType.HTML:
            return generate_html_page(
                rdf_graph,
                data_catalog_uri,
                current_app.config.get("SPARQL_ENDPOINT", ""),
            )
        else:
            # another serialisation than HTML
            return get_serialised_graph(rdf_graph, mime_type)

    def is_data_catalog(self, data_catalog_uri: str) -> bool:
        return DataCatalogLODHandler().is_data_catalog(data_catalog_uri)

    def is_valid_data_catalog(self, data_catalog_uri: str) -> bool:
        return DataCatalogLODHandler().is_valid_data_catalog(data_catalog_uri)


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
class LODDataDownloadAPI(Resource):
    """Serve the RDF for the data downloads in the format that was requested."""

    @api.produces([mt.value for mt in MimeType])
    def get(self, number: str = ""):
        """Get the RDF for the DataDownload."""

        # check if number is an integer value
        if not number.isdigit():
            return APIUtil.toErrorResponse(
                "bad_request", f"Invalid identifier supplied: {number}"
            )

        # get B&G lod resource iri
        data_download_uri = util.ld_util.generate_lod_resource_uri(
            DatasetApiUriLevel.DATADOWNLOAD,
            number,
            current_app.config["BENG_DATA_DOMAIN"],
        )

        # check if resource exists
        if self.is_data_download(data_download_uri) is False:
            logger.error(f"Data download does not exist: {data_download_uri}")
            return APIUtil.toErrorResponse("not_found")

        # check if data download is valid
        if not self.is_valid_data_download(data_download_uri):
            logger.error(f"Invalid data download: {data_download_uri}")
            return APIUtil.toErrorResponse("bad_request", "Invalid DataDownload")

        # get the requested mime_type
        lod_server_supported_mime_types = [mt.value for mt in MimeType]
        best_match = request.accept_mimetypes.best_match(
            lod_server_supported_mime_types
        )
        mime_type = (
            MimeType.JSON_LD
        )  # we choose to set a default if the user has not specified
        if best_match is not None:
            mime_type = MimeType(best_match)

        # get rdf
        logger.info(f"Getting RDF for resource {data_download_uri} from triple store.")
        rdf_graph = Graph()
        dd_data = DataCatalogLODHandler().get_data_download(
            data_download_uri, MimeType.TURTLE.value
        )
        rdf_graph.parse(data=dd_data, format=MimeType.TURTLE.value)
        if not rdf_graph:
            return APIUtil.toErrorResponse(
                "internal_server_error",
                f"No graph created. Check resource type and identifier for {data_download_uri}",
            )

        # generate and return response
        if mime_type is MimeType.HTML:
            return generate_html_page(
                rdf_graph,
                data_download_uri,
                current_app.config.get("SPARQL_ENDPOINT", ""),
            )
        else:
            # another serialisation than HTML
            return get_serialised_graph(rdf_graph, mime_type)

    def is_data_download(self, data_download_uri: str) -> bool:
        return DataCatalogLODHandler().is_data_download(data_download_uri)

    def is_valid_data_download(self, data_download_uri: str) -> bool:
        return DataCatalogLODHandler().is_valid_data_download(data_download_uri)
