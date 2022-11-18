import logging
from rdflib import URIRef
from rdflib import Graph
from rdflib.namespace import RDF, SDO
from apis.mime_type_util import MimeType
from typing import List, Optional
from util.ld_util import sparql_construct_query
from datetime import datetime, timedelta


class DataCatalogLODHandler:
    """Handles requests from the beng-lod server for data catalogs, datasets, datadownloads.
    The only data model/ontology this data is available in is schema.org. In contrast with the resource
    endpoint it doesn't take the profile parameter from the Accept header into consideration.
    The source for the data catalog is a (Turtle) file in /resource.
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(config["LOG_NAME"])
        self.cache = config["GLOBAL_CACHE"]
        sparql_endpoint = self.config.get("SPARQL_ENDPOINT")
        self._data_catalog = self._get_data_catalog_from_store(sparql_endpoint)

    def _get_data_catalog_from_store(
        self, sparql_endpoint: str, cache_key: str = "data_catalog", minutes: int = 60
    ) -> Graph:
        """Get data catalog triples from the rdf store and return graph. Simple caching
        is enabled as well as a simple expiration mechanism for the cache."""
        cache_key_expiration = f"{cache_key}_expiration"
        if cache_key_expiration in self.cache:
            if datetime.utcnow() >= self.cache[cache_key_expiration]:
                self.logger.debug(
                    f"The cache for {cache_key} is expired. Emptying cache."
                )
                del self.cache[cache_key]
                del self.cache[cache_key_expiration]

        if cache_key in self.cache:
            self.logger.debug(f"GOT THE {cache_key} FROM CACHE")
            return self.cache[cache_key]
        else:
            self.logger.debug(f"NO {cache_key} FOUND IN CACHE")
            self.logger.info(f"Getting data catalog triples from '{sparql_endpoint}'")
            construct_query = (
                "CONSTRUCT { ?sub ?pred ?obj } WHERE { "
                "GRAPH <http://data.rdlabs.beeldengeluid.nl/datacatalog/> { ?sub ?pred ?obj } }"
            )
            self.logger.debug(f"Sending query '{construct_query}'")
            graph = sparql_construct_query(sparql_endpoint, construct_query)
            self.cache[cache_key] = graph
            self.logger.debug(f"Added cache for {cache_key}.")
            cache_lifetime = timedelta(minutes=minutes)
            self.cache[cache_key_expiration] = datetime.utcnow() + cache_lifetime
            self.logger.debug(
                f"Set expiration for '{cache_key}': {str(self.cache[cache_key_expiration])}."
            )
            return graph

    """-------------NDE requirements validation----------------------"""

    def is_valid_data_download(self, data_download_id: str) -> bool:
        """Checks whether the data download has the minimal required information.

        A DataDownload has a minimal definition:
          - an IRI
          - contentUrl
          - encodingFormat
          - usageInfo (if the distribution is non-standard API)
        """
        if (
            self.is_data_download(data_download_id)
            and self.has_content_url(data_download_id)
            and self.has_encoding_format(data_download_id)
            and self.has_usage_info(data_download_id)
        ):
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
        if (
            self.is_dataset(dataset_id)
            and self.has_name(dataset_id)
            and self.has_license(dataset_id)
            and self.has_publisher(dataset_id)
            and self.has_distribution(dataset_id)
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
        if (
            self.is_data_catalog(data_catalog_id)
            and self.has_name(data_catalog_id)
            and self.has_publisher(data_catalog_id)
            and self.has_dataset(data_catalog_id)
        ):
            return True
        return False

    def is_valid_organization(self, organization_id: str) -> bool:
        """Validates whether the Organization has the minimal required properties.

        An Organization as publisher has at least:
          - an IRI
          - a name
        """
        if self.is_organization(URIRef(organization_id)) and self.has_name(
            organization_id
        ):
            return True
        return False

    def has_name(self, some_uri: str) -> bool:
        """Check whether the resource has a name."""
        if some_uri is None:
            return False
        return (URIRef(some_uri), SDO.name, None) in self._data_catalog

    def has_license(self, dataset_id: str) -> bool:
        """Check whether the dataset has a proper license."""
        if dataset_id is None:
            return False
        return (URIRef(dataset_id), SDO.license, None) in self._data_catalog

    def has_publisher(self, resource_id: str) -> bool:
        """Check whether the resource has a publisher."""
        if resource_id is None:
            return False
        return (URIRef(resource_id), SDO.publisher, None) in self._data_catalog

    def has_distribution(self, dataset_id: str) -> bool:
        """Check whether the dataset has a distribution."""
        if dataset_id is None:
            return False
        return (URIRef(dataset_id), SDO.distribution, None) in self._data_catalog

    def has_content_url(self, data_download_id: str) -> bool:
        """Check whether the data download has a content URL."""
        if data_download_id is None:
            return False
        return (URIRef(data_download_id), SDO.contentUrl, None) in self._data_catalog

    def has_encoding_format(self, data_download_id: str) -> bool:
        """Check whether the data download has an encoding format."""
        if data_download_id is None:
            return False
        return (
            URIRef(data_download_id),
            SDO.encodingFormat,
            None,
        ) in self._data_catalog

    def has_usage_info(self, data_download_id: str) -> bool:
        """Check whether the data download has usage info."""
        if data_download_id is None:
            return False
        return (URIRef(data_download_id), SDO.usageInfo, None) in self._data_catalog

    def is_data_download(self, data_download_id: str) -> bool:
        """Check if data download exists."""
        if data_download_id is None:
            return False
        return (
            URIRef(data_download_id),
            RDF.type,
            SDO.DataDownload,
        ) in self._data_catalog

    def has_dataset(self, data_catalog_id: str) -> bool:
        """Check whether the data catalog has a dataset."""
        if data_catalog_id is None:
            return False
        return (URIRef(data_catalog_id), SDO.dataset, None) in self._data_catalog

    """------------LOD Handler functions---------------"""

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
        return g.serialize(format=mime_format, auto_compact=True)

    def is_data_catalog(self, data_catalog_uri: str) -> bool:
        """Check if data catalog exists"""
        if data_catalog_uri is None:
            return False
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
        return g.serialize(
            format=mime_format,
            auto_compact=True,
        )

    def is_dataset(self, dataset_uri: str) -> bool:
        """Check if dataset exists"""
        if dataset_uri is None:
            return False
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

        return g.serialize(format=mime_format, auto_compact=True)

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
        """Return a list of dataset_id's that are in the data datalog."""
        return [
            str(dataset_obj)
            for dataset_obj in self._data_catalog.objects(
                URIRef(data_catalog_id), SDO.dataset
            )
            if self.is_valid_dataset(str(dataset_obj))
        ]

    def get_data_downloads_for_dataset(self, dataset_id: str) -> List:
        """Return a list of data_downloads_id's that are in the dataset."""
        return [
            data_download_obj
            for data_download_obj in self._data_catalog.objects(
                URIRef(dataset_id), SDO.distribution
            )
            if self.is_valid_data_download(str(data_download_obj))
        ]

    def get_publisher_for_data_catalog(
        self, data_catalog_id: URIRef
    ) -> Optional[URIRef]:
        """Return the URI for the organization that is the publisher of the DataCatalog."""
        return self._data_catalog.value(URIRef(data_catalog_id), SDO.publisher)

    def is_organization(self, organization_id: URIRef) -> bool:
        """Check whether organization exists in data catalog."""
        if organization_id is None:
            return False
        return (organization_id, RDF.type, SDO.Organization) in self._data_catalog

    def get_organization_triples(self, organization_id: URIRef) -> Graph:
        """Returns a Graph with the triples for the organization."""
        g = Graph()
        g.bind("sdo", SDO)
        if self.is_organization(organization_id) is False:
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
