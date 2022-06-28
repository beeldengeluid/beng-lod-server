import logging
from util.APIUtil import APIUtil
from rdflib import URIRef
from rdflib import Graph
from rdflib.namespace import RDF, SDO
from apis.mime_type_util import MimeType


class DataCatalogLODHandler:
    """Handles requests from the beng-lod server for data catalogs, datasets, datadownloads.
    The only data model/ontology this data is available in is schema.org. In contrast with the resource
    endpoint it doesn't take the profile parameter from the Accept header into consideration.
    The source for the data catalog is a (Turtle) file in /resource.
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(config["LOG_NAME"])
        self._data_catalog = None
        self._init_data_catalog(config["DATA_CATALOG_FILE"])

    # TODO: implement caching suitable for this function
    def _init_data_catalog(self, data_catalog_file: str):
        """When initialized, get the data file from /resource."""
        self.logger.info("Loading data catalogue")
        self._data_catalog = Graph()
        import git
        import pathlib

        repo = git.Repo(".", search_parent_directories=True)
        git_src_dir = pathlib.Path(repo.working_tree_dir).joinpath(  # type: ignore #TODO working_tree_dir can be None
            "src"
        )
        data_catalog_unit_test_file = (
            pathlib.Path(git_src_dir).joinpath(data_catalog_file).absolute().as_uri()
        )

        self._data_catalog.parse(
            data_catalog_unit_test_file, format=MimeType.TURTLE.value
        )

    """-------------NDE requirements validation----------------------"""

    def is_valid_data_download(self, data_download_id):
        """Checks whether the data download has the minimal required information.

        A DataDownload has a minimal definition:
          - contentUrl
          - encodingFormat
          - what about the @id? #TODO
          - usageInfo (if the distribution is non-standard API)
        """
        has_content_url = (
            URIRef(data_download_id),
            SDO.contentUrl,
            None,
        ) in self._data_catalog
        has_encoding_format = (
            URIRef(data_download_id),
            SDO.encodingFormat,
            None,
        ) in self._data_catalog
        has_usage_info = (
            URIRef(data_download_id),
            SDO.usageInfo,
            None,
        ) in self._data_catalog

        if has_content_url and has_encoding_format and has_usage_info:
            return True
        return False

    def is_valid_dataset(self, dataset_id):
        """Checks whether the dataset qualifies according to the NDE requirements for datasets.

        A Dataset MUST have:
          - an IRI
          - a name
          - a license IRI

        and it SHOULD have:
          - a publisher
          - at least one distribution
        """
        has_iri = (URIRef(dataset_id), RDF.type, SDO.Dataset) in self._data_catalog
        has_name = (URIRef(dataset_id), SDO.name, None) in self._data_catalog
        has_license_iri = (URIRef(dataset_id), SDO.license, None) in self._data_catalog
        has_publisher = (URIRef(dataset_id), SDO.publisher, None) in self._data_catalog
        has_distribution = (
            URIRef(dataset_id),
            SDO.distribution,
            None,
        ) in self._data_catalog
        if (
            has_iri
            and has_name
            and has_license_iri
            and has_publisher
            and has_distribution
        ):
            return True
        return False

    def is_valid_data_catalog(self, data_catalog_id):
        """Checks if the data catalog has at least got the minimal required properties.

        The DataCatalog has at least:
          - an IRI
          - a name
          - a publisher
          - at least one dataset
        """
        has_iri = (
            URIRef(data_catalog_id),
            RDF.type,
            SDO.DataCatalog,
        ) in self._data_catalog
        has_name = (URIRef(data_catalog_id), SDO.name, None) in self._data_catalog
        has_publisher = (
            URIRef(data_catalog_id),
            SDO.publisher,
            None,
        ) in self._data_catalog
        has_dataset = (URIRef(data_catalog_id), SDO.dataset, None) in self._data_catalog

        if has_iri and has_name and has_publisher and has_dataset:
            return True
        return False

    def is_valid_organization(self, organization_id):
        """Validates whether the Organization has the minimal required properties.

        An Organization as publisher has at least:
          - an IRI
          - a name
        """
        has_iri = (
            URIRef(organization_id),
            RDF.type,
            SDO.Organization,
        ) in self._data_catalog
        has_name = (URIRef(organization_id), SDO.name, None) in self._data_catalog
        if has_iri and has_name:
            return True
        return False

    """------------LOD Handler functions---------------"""

    def get_data_download(self, data_download_id, mime_format=MimeType.JSON_LD.value):
        """Get the triples for a DataDownload.
        :param data_download_id: the id of a DataDownload, originating from the spreadsheet. Must be a URI.
        :param mime_format: mime_type for the data response.
        :returns: The triples (or the Graph?)  for the DataDownload.
        """
        if not (URIRef(data_download_id), None, None) in self._data_catalog:
            return APIUtil.toErrorResponse("not_found")

        g = Graph()
        g.bind("sdo", SDO)

        # load the triples for the data download
        for triple in self.triples_data_download(data_download_uri=data_download_id):
            g.add(triple)

        # now return the collected triples in the requested format
        json_string = g.serialize(
            format=mime_format,
            auto_compact=True,
        )
        if json_string:
            return APIUtil.toSuccessResponse(json_string)
        return APIUtil.toErrorResponse("bad_request", "Invalid URI or return format")

    def get_data_catalog(self, data_catalog_uri, mime_format=MimeType.JSON_LD.value):
        """Returns the data from the data catalog graph in requested serialization format.
        :param data_catalog_uri: the identifier for the data catalog
        :param mime_format: the requested mime type for the graph data. Defaults to JSON-LD.
        """
        # check if resource exists
        if not (URIRef(data_catalog_uri), None, None) in self._data_catalog:
            return APIUtil.toErrorResponse("not_found")

        g = Graph()
        g.bind("sdo", SDO)

        # add triples for the data_catalog
        for triple in self.triples_data_catalog(data_catalog_uri=data_catalog_uri):
            g.add(triple)

        # add triples for the organization
        organization_id = self.get_organization_for_data_catalog(
            data_catalog_id=data_catalog_uri
        )
        for triple in self.triples_organization(organization_id=organization_id):
            g.add(triple)

        # add triples for each dataset
        for dataset_uri in self.get_datasets_for_data_catalog(
            data_catalog_id=data_catalog_uri
        ):
            for triple in self.triples_dataset(dataset_uri=dataset_uri):
                g.add(triple)

            # add the triples for the organization
            organization_id = self.get_organization_for_dataset(dataset_id=dataset_uri)
            for triple in self.triples_organization(organization_id=organization_id):
                g.add(triple)

            # add triples for each data download
            for data_download_id in self.get_data_downloads_for_dataset(
                dataset_id=dataset_uri
            ):
                for triple in self.triples_data_download(
                    data_download_uri=data_download_id
                ):
                    g.add(triple)

        # now return the collected triples in the requested format
        json_string = g.serialize(
            format=mime_format,
            auto_compact=True,
        )

        if json_string:
            return APIUtil.toSuccessResponse(json_string)
        return APIUtil.toErrorResponse("bad_request", "Invalid URI or return format")

    def get_dataset(self, dataset_uri, mime_format="json-ld"):
        """Returns the data from the data catalog graph in requested serialization format.
        :param dataset_uri: the identifier for the dataset
        :param mime_format: the requested mime type for the graph data. Defaults to JSON-LD.
        """
        # check if resource exists
        if not (URIRef(dataset_uri), None, None) in self._data_catalog:
            return APIUtil.toErrorResponse("not_found")

        g = Graph()
        g.bind("sdo", SDO)

        if self.is_valid_dataset(dataset_uri):

            # add triples for the dataset
            for triple in self.triples_dataset(dataset_uri=dataset_uri):
                g.add(triple)

            # get triples for all the data downloads in the dataset
            for data_download_id in self.get_data_downloads_for_dataset(dataset_uri):
                for triple in self.triples_data_download(
                    data_download_uri=data_download_id
                ):
                    g.add(triple)

            # add the triples for the organization
            organization_id = self.get_organization_for_dataset(dataset_id=dataset_uri)
            for triple in self.triples_organization(organization_id=organization_id):
                g.add(triple)

        json_string = g.serialize(
            format=mime_format,
            auto_compact=True,
        )
        if json_string:
            return APIUtil.toSuccessResponse(json_string)
        return APIUtil.toErrorResponse("bad_request", "Invalid URI or return format")

    """------------Triples filters---------------"""

    def triples_data_download(self, data_download_uri):
        """Returns a generator over the triples for the data download."""
        if data_download_uri is None:
            return None
        data_download_triples = self._data_catalog.triples(
            (URIRef(data_download_uri), None, None)
        )
        return data_download_triples if data_download_triples is not None else None

    def triples_dataset(self, dataset_uri):
        """Returns a generator over the triples for the dataset. It includes the triples for the dataset."""
        if dataset_uri is None:
            return None
        dataset_triples = self._data_catalog.triples((URIRef(dataset_uri), None, None))
        return dataset_triples if dataset_triples is not None else None

    def triples_data_catalog(self, data_catalog_uri):
        """Returns a generator over the triples for the data catalog."""
        if data_catalog_uri is None:
            return None
        triples_data_catalog = self._data_catalog.triples(
            (URIRef(data_catalog_uri), None, None)
        )
        return triples_data_catalog if triples_data_catalog is not None else None

    def triples_organization(self, organization_id):
        """Returns a generator over the triples for the organization."""
        if organization_id is None:
            return None
        organization_triples = self._data_catalog.triples(
            (URIRef(organization_id), None, None)
        )
        return organization_triples if organization_triples is not None else None

    """-------------parts of functions------------------"""

    def get_datasets_for_data_catalog(self, data_catalog_id):
        """Return a list of dataset_id's that are a dataset for the data datalog."""
        list_of_datasets = []
        for dataset_obj in self._data_catalog.objects(
            URIRef(data_catalog_id), SDO.dataset
        ):
            if self.is_valid_dataset(dataset_id=dataset_obj):
                list_of_datasets.append(dataset_obj)
        return list_of_datasets

    def get_data_downloads_for_dataset(self, dataset_id):
        """Return a list of data_downloads_id's that are a distribution of the dataset."""
        list_of_distributions = []
        for data_download_obj in self._data_catalog.objects(
            URIRef(dataset_id), SDO.distribution
        ):
            if self.is_valid_data_download(data_download_id=data_download_obj):
                list_of_distributions.append(data_download_obj)
        return list_of_distributions

    def get_organization_for_data_catalog(self, data_catalog_id):
        """Return the URI for the organization that is the publisher of the DataCatalog."""
        return self._data_catalog.value(URIRef(data_catalog_id), SDO.publisher)

    def get_organization_for_dataset(self, dataset_id):
        """Return the URI for the organization that is the publisher of the Dataset."""
        return self._data_catalog.value(URIRef(dataset_id), SDO.publisher)
