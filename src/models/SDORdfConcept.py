import models.SDORdfModel as schema
from rdflib.namespace import RDF, SKOS, Namespace
from rdflib import Graph, URIRef
from util.APIUtil import APIUtil
from apis.lod.SDOSchemaImporter import SDOSchemaImporter
from cache import cache
from urllib.parse import urlparse, urlunparse
from models.BaseRdfConcept import BaseRdfConcept

nisvSchemaNamespace = Namespace(schema.NISV_SCHEMA_NAMESPACE)
schemaOrgNamespace = Namespace(schema.SCHEMA_DOT_ORG_NAMESPACE)
nisvDataNamespace = Namespace(schema.NISV_DATA_NAMESPACE)
gtaaNamespace = Namespace(schema.GTAA_NAMESPACE)
nonGtaaNamespace = Namespace(schema.NON_GTAA_NAMESPACE)


def get_uri(cat_type="PROGRAM", daan_id=None):
    if daan_id is None:
        return None
    url_parts = urlparse(schema.NISV_DATA_NAMESPACE)
    path = '/'.join(['resource', cat_type.lower(), daan_id])
    parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
    return urlunparse(parts)


class SDORdfConcept(BaseRdfConcept):
    """ Class to represent an NISV catalog object in RDF.
        It uses functions to create the RDF in a graph using the JSON payload from the Direct Access Metadata API.
    """

    def __init__(self, metadata, concept_type, config):
        super().__init__(config)
        self.config = config
        if "SCHEMA_DOT_ORG" not in self.config or "MAPPING_FILE_SDO" not in self.config:
            raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'Schema or mapping file not specified')

        self.graph = Graph()
        self.graph.namespace_manager.bind(schema.NISV_SCHEMA_PREFIX, nisvSchemaNamespace)
        self.graph.namespace_manager.bind(schema.SCHEMA_DOT_ORG_PREFIX, schemaOrgNamespace)
        self.graph.namespace_manager.bind(schema.NISV_DATA_PREFIX, nisvDataNamespace)
        self.graph.namespace_manager.bind("skos", SKOS)
        self.graph.namespace_manager.bind("gtaa", gtaaNamespace)
        self.graph.namespace_manager.bind("non-gtaa", nonGtaaNamespace)

        # create a node for the record
        self.itemNode = URIRef(get_uri(cat_type=concept_type, daan_id=metadata['id']))

        # get the RDF class URI for this type
        self.classUri = schema.CLASS_URIS_FOR_DAAN_LEVELS[concept_type]

        # add the type
        self.graph.add((self.itemNode, RDF.type, URIRef(self.classUri)))

        # convert the record payload to RDF
        self.__payloadToRdf(metadata["payload"], self.itemNode, self.classUri)

        # create RDF relations with the parents of the record
        self.__parentToRdf(metadata)

        # do this after the sub-class is initialized
        self._post_init()

    @cache.cached(timeout=0, key_prefix='sdo_scheme')
    def get_scheme(self):
        """ Override from the base class, to make it specific for schema.org."""
        return SDOSchemaImporter(self.config["SCHEMA_DOT_ORG"], self.config["MAPPING_FILE_SDO"])
