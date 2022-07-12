import logging
from rdflib import URIRef
from rdflib import Graph
from rdflib.namespace import RDF, SDO
from apis.mime_type_util import MimeType
from typing import List, Optional


class DataCatalogLODHandler:
    """Handles requests from the beng-lod server for data catalogs, datasets, datadownloads.
    The only data model/ontology this data is available in is schema.org. In contrast with the resource
    endpoint it doesn't take the profile parameter from the Accept header into consideration.
    The source for the data catalog is a (Turtle) file in /resource.
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(config["LOG_NAME"])
        self._data_catalog = self._parse_catalog_file(config["DATA_CATALOG_FILE"])

    # TODO: implement caching suitable for this function
    def _parse_catalog_file(self, path: str) -> Graph:
        """Parse catalog file (turtle) and return graph of results'"""
        self.logger.info(f"Loading data catalogue from '{path}'")
        graph = Graph().parse(path, format=MimeType.TURTLE.value)
        return graph

    """-------------NDE requirements validation----------------------"""

    def is_valid_data_download(self, data_download_id: str) -> bool:
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

    def is_valid_dataset(self, dataset_id: str) -> bool:
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

    def is_valid_data_catalog(self, data_catalog_id: str) -> bool:
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

    def is_valid_organization(self, organization_id: str) -> bool:
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

    def is_data_download(self, data_download_id: str) -> bool:
        """Check if data download exists."""
        return (
            URIRef(data_download_id),
            RDF.type,
            SDO.DataDownload,
        ) in self._data_catalog

    def get_data_download(
        self, data_download_id: str, mime_format: str = "json-ld"
    ) -> str:
        """Get the triples for a DataDownload.
        :param data_download_id: the id of a DataDownload, originating from the spreadsheet. Must be a URI.
        :param mime_format: the required mime_type to return
        :returns: The Graph for the DataDownload.
        """
        g = Graph()
        g.bind("sdo", SDO)
        for triple in self._data_catalog.triples(
            (URIRef(data_download_id), None, None)
        ):
            g.add(triple)

        # now return the collected triples in the requested format
        res_string = g.serialize(
            format=mime_format,
            auto_compact=True,
        )
        return res_string

    def is_data_catalog(self, data_catalog_uri: str) -> bool:
        """Check if data catalog exists"""
        return (
            URIRef(data_catalog_uri),
            RDF.type,
            SDO.DataCatalog,
        ) in self._data_catalog

    def get_data_catalog(self, data_catalog_uri, mime_format=MimeType.JSON_LD.value):
        """Returns the data from the data catalog graph in requested serialization format.
        :param data_catalog_uri: the identifier for the data catalog
        :param mime_format: the requested mime type for the graph data. Defaults to JSON-LD.
        """
        g = Graph()
        g.bind("sdo", SDO)

        # add triples for the data_catalog
        g += self.get_data_catalog_triples(URIRef(data_catalog_uri))

        # add triples for the publisher
        publisher_id = self.get_publisher_for_data_catalog(URIRef(data_catalog_uri))
        g += self.get_organization_triples(publisher_id)

        # add triples for each dataset
        for dataset_uri in self.get_datasets_for_data_catalog(URIRef(data_catalog_uri)):
            g += self.get_dataset_triples(URIRef(dataset_uri))

        # now serialize the collected triples in the requested format
        res_string = g.serialize(
            format=mime_format,
            auto_compact=True,
        )
        return res_string

    def is_dataset(self, dataset_uri: str) -> bool:
        """Check if dataset exists"""
        return (
            URIRef(dataset_uri),
            RDF.type,
            SDO.Dataset,
        ) in self._data_catalog

    def get_dataset(self, dataset_uri: str, mime_format: str = "json-ld") -> str:
        """Returns the data from the data catalog graph in requested serialization format.
        :param dataset_uri: the identifier for the dataset
        :param mime_format: the requested mime type for the graph data. Defaults to JSON-LD.
        """
        g = Graph()
        g.bind("sdo", SDO)

        # add triples for the dataset
        g += self.get_dataset_triples(URIRef(dataset_uri))

        res_string = g.serialize(
            format=mime_format,
            auto_compact=True,
        )
        return res_string

    """------------Triples filters---------------"""

    def get_data_download_triples(self, data_download_uri: URIRef) -> Graph:
        """Adds the triples for the data download to a Graph."""
        g = Graph()
        g.bind("sdo", SDO)
        for triple in self._data_catalog.triples((data_download_uri, None, None)):
            g.add(triple)
        return g

    def get_dataset_triples(self, dataset_uri: URIRef) -> Graph:
        """Returns the graph containing all triples for a dataset."""
        g = Graph()
        g.bind("sdo", SDO)

        # add triples related to the dataset itself
        for triple in self._data_catalog.triples((dataset_uri, None, None)):
            g.add(triple)

        # add the triples for the publisher
        publisher_id = self.get_publisher_for_dataset(dataset_uri)
        g += self.get_organization_triples(publisher_id)

        # if the dataset has a creator, add the triples for the creator organization
        creator_id = self.get_creator_for_dataset(dataset_uri)
        if creator_id is not None:
            g += self.get_organization_triples(creator_id)

        # get triples for all the data downloads in the dataset
        for data_download_id in self.get_data_downloads_for_dataset(dataset_uri):
            g += self.get_data_download_triples(data_download_id)

        return g

    def get_data_catalog_triples(self, data_catalog_uri: URIRef) -> Graph:
        """Adds the triples for a datasets to a Graph and returns the Graph."""
        g = Graph()
        g.bind("sdo", SDO)
        for triple in self._data_catalog.triples((data_catalog_uri, None, None)):
            g.add(triple)
        return g

    """------------- get aggregates ------------------"""

    def get_datasets_for_data_catalog(self, data_catalog_id: str) -> List:
        """Return a list of dataset_id's that are a dataset for the data datalog."""
        list_of_datasets = []
        for dataset_obj in self._data_catalog.objects(
            URIRef(data_catalog_id), SDO.dataset
        ):
            if self.is_valid_dataset(dataset_obj):
                list_of_datasets.append(dataset_obj)
        return list_of_datasets

    def get_data_downloads_for_dataset(self, dataset_id: str) -> List[URIRef]:
        """Return a list of data_downloads_id's that are a distribution of the dataset."""
        list_of_distributions = []
        for data_download_obj in self._data_catalog.objects(
            URIRef(dataset_id), SDO.distribution
        ):
            if self.is_valid_data_download(data_download_obj):
                list_of_distributions.append(data_download_obj)
        return list_of_distributions

    def get_publisher_for_data_catalog(
        self, data_catalog_id: URIRef
    ) -> Optional[URIRef]:
        """Return the URI for the organization that is the publisher of the DataCatalog."""
        return self._data_catalog.value(URIRef(data_catalog_id), SDO.publisher)

    def is_organization(self, organization_id: URIRef) -> bool:
        """Check whether organization exists in data catalog."""
        return (organization_id, RDF.type, SDO.Organization) in self._data_catalog

    def get_organization_triples(self, organization_id: URIRef) -> Graph:
        """Returns a Graph with the triples for the organization."""
        g = Graph()
        g.bind("sdo", SDO)
        if organization_id is None or self.is_organization(organization_id) is False:
            return g
        for triple in self._data_catalog.triples((organization_id, None, None)):
            g.add(triple)
        return g

    def get_publisher_for_dataset(self, dataset_id: URIRef) -> URIRef:
        """Return the URI for the organization that is the publisher of the Dataset."""
        return self._data_catalog.value(dataset_id, SDO.publisher)

    def get_creator_for_dataset(self, dataset_id: URIRef) -> URIRef:
        """Return the URI for the Organization that is the creator of the Dataset."""
        return self._data_catalog.value(dataset_id, SDO.creator)
