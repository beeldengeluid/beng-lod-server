import models.DAANRdfModel as schema
from models.DAANJsonModel import DAAN_PROGRAM_ID, DAAN_PARENT, DAAN_PARENT_ID, DAAN_PARENT_TYPE, DAAN_PAYLOAD, \
    ObjectType
from rdflib.namespace import RDF, RDFS, SKOS, Namespace, NamespaceManager
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.plugin import PluginException
from util.APIUtil import APIUtil
from apis.lod.SDOSchemaImporter import SDOSchemaImporter
from cache import cache
from urllib.parse import urlparse, urlunparse


def get_uri(cat_type="PROGRAM", daan_id=None):
    if daan_id is None:
        return None
    url_parts = urlparse(schema.NISV_DATA_NAMESPACE)
    path = '/'.join(['resource', cat_type.lower(), daan_id])
    parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
    return urlunparse(parts)


class SDORdfConcept:
    """ Class to represent an NISV catalog object in RDF.
        It uses functions to create the RDF in a graph using the JSON payload from the Direct Access Metadata API.

    """

    def __init__(self, metadata, concept_type, config):

        # check config
        self.config = config
        if "SCHEMA_FILE" not in self.config or "MAPPING_FILE" not in self.config:
            raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'Schema or mapping file not specified')

        self._schema = self.get_sdo_scheme()
        self._classes = self._schema.getClasses()

        assert self._classes is not None, APIUtil.raiseDescriptiveValueError('internal_server_error',
                                                                             'Error while loading the schema classes and properties')

        nisvSchemaNamespace = Namespace(schema.NISV_SCHEMA_NAMESPACE)
        nisvDataNamespace = Namespace(schema.NISV_DATA_NAMESPACE)
        gtaaNamespace = Namespace(schema.GTAA_NAMESPACE)
        nonGtaaNamespace = Namespace(schema.NON_GTAA_NAMESPACE)

        self.graph = Graph()
        self.graph.namespace_manager.bind(schema.NISV_SCHEMA_PREFIX, nisvSchemaNamespace)
        self.graph.namespace_manager.bind(schema.NISV_DATA_PREFIX, nisvDataNamespace)
        self.graph.namespace_manager.bind("skos", SKOS)
        self.graph.namespace_manager.bind("gtaa", gtaaNamespace)
        self.graph.namespace_manager.bind("non-gtaa", nonGtaaNamespace)

        # create a node for the record
        resource_path = '/'.join([concept_type.lower(), metadata["id"]])
        self.itemNode = URIRef(schema.NISV_DATA_NAMESPACE + resource_path)

        # get the RDF class URI for this type
        self.classUri = schema.CLASS_URIS_FOR_DAAN_LEVELS[concept_type]

        # add the type
        self.graph.add((self.itemNode, RDF.type, URIRef(self.classUri)))

        # convert the record payload to RDF
        self.__payloadToRdf(metadata["payload"], self.itemNode, self.classUri)

        # create RDF relations with the parents of the record
        self.__parentToRdf(metadata)

    @cache.cached(timeout=0, key_prefix='sdo_scheme')
    def get_sdo_scheme(self):
        return SDOSchemaImporter(self.config["SCHEMA_DOT_ORG"], self.config["MAPPING_FILE_SDO"])

    def __getMetadataValue(self, metadata, metadataField):
        """ Gets the value of the metadata field from the JSON metadata.
            Returns either a single value, or a list of multiple values
        """

        if "," in metadataField:
            fieldParts = metadataField.split(",")

            if type(metadata) is not list:
                valueList = [metadata]  # create a list as the metadata field could contain a list at some point
            else:
                valueList = metadata

            for part in fieldParts:
                part = part.strip()  # remove any whitespace
                newValueList = []
                found = False
                for value in valueList:
                    if value:
                        if part in value:
                            found = True
                            if type(value[part]) is list:
                                newValueList.extend(value[part])
                            else:
                                newValueList.append(value[part])
                if not found:
                    return ""  # no value for the metadata field
                valueList = newValueList

            return valueList
        else:
            if metadataField in metadata:
                return metadata[metadataField]
            else:
                return ""

    def __payloadToRdf(self, payload, parentNode, classUri):
        """Converts the metadata described in payload (json) to RDF, and attaches it to the parentNode
        (e.g. the parentNode can be the identifier node for a program, and the payload the metadata describing
        that program.). Calls itself recursively to handle any classes in the metadata, e.g. the publication
        belonging to a program.
        Uses the classUri of the parent node to select the right information from  classes for the conversion.
        Returns the result in graph
        """

        # Select the relevant properties for this type of parent using the classUri
        properties = self._classes[classUri]["properties"]

        # retrieve metadata for each relevant property
        for uri, rdfProperty in properties.items():

            # try each possible path for the property until find some metadata
            newPayload = None
            for path in rdfProperty["paths"]:
                newPayload = self.__getMetadataValue(payload, path)
                usedPath = path
                if newPayload:
                    break

            # if we found metadata for this property
            if newPayload:
                if type(newPayload) is not list:
                    newPayload = [newPayload]  # we can have a list of metadata, so make sure it is always
                # a list for consistent handling

                # for each item in the metadata list
                for newPayloadItem in newPayload:
                    # if range of property is simple data type, just link it to the parent using the property
                    if rdfProperty["range"] in schema.XSD_TYPES:
                        self.graph.add((parentNode, URIRef(uri), Literal(newPayloadItem, datatype=rdfProperty[
                            "range"])))  # add the new payload as the value
                    elif rdfProperty["rangeSuperClass"] == schema.ACTING_ENTITY or rdfProperty[
                        "rangeSuperClass"] == str(SKOS.Concept):
                        # In these cases, we have a class as range, but only a simple value in DAAN, as we want to model a label
                        #  from DAAN with a skos:Concept in the RDF
                        # create a node for the skos concept

                        # TODO: check the consistency of usedPath
                        # look one step higher to be able to get to the ID of a thesaurus item
                        if "," in usedPath:
                            classPath = ",".join(usedPath.split(",")[:-1])
                            conceptMetadata = self.__getMetadataValue(payload, classPath)

                            # the value could be a list, so make sure it always is so can treat everything the same way
                            if type(conceptMetadata) is not list:
                                conceptMetadata = [conceptMetadata]

                        conceptNode = None
                        for concept in conceptMetadata:
                            if "origin" in concept and "value" in concept and "resolved_value" in concept:
                                if concept["resolved_value"] == newPayloadItem:
                                    # we have a thesaurus concept and can use the value to generate the URI
                                    if rdfProperty["range"] in schema.NON_GTAA_TYPES:
                                        conceptNode = URIRef(schema.NON_GTAA_NAMESPACE + concept["value"])
                                    else:
                                        conceptNode = URIRef(schema.GTAA_NAMESPACE + concept["value"])
                                skosConcept = True
                        if not conceptNode:
                            # we only have a label, so we create a blank node
                            conceptNode = BNode()
                            skosConcept = False

                        self.graph.add((conceptNode, RDF.type, URIRef(rdfProperty["range"])))
                        self.graph.add((parentNode, URIRef(uri), conceptNode))  # link it to the parent

                        if skosConcept:
                            # set the pref label of the concept node to be the DAAN payload item
                            self.graph.add((conceptNode, SKOS.prefLabel, Literal(newPayloadItem, lang="nl")))
                        else:
                            # set the rdfs label of the concept node to be the DAAN payload item
                            self.graph.add((conceptNode, RDFS.label, Literal(newPayloadItem, lang="nl")))
                    else:
                        # we have a class as range
                        # create a blank node for the class ID, and a triple to set the type of the class
                        blankNode = BNode()
                        self.graph.add((blankNode, RDF.type, URIRef(rdfProperty["range"])))
                        self.graph.add((parentNode, URIRef(uri), blankNode))  # link it to the parent
                        # and call the function again to handle the properties for the class
                        self.__payloadToRdf(newPayloadItem, blankNode, rdfProperty["range"])

        return

    def __parentToRdf(self, metadata):
        """Depending on the type of the child (e.g. program) retrieve the information about its
        parents from the metadata, link the child to the parents, and return the new instances and
        properties in the graph"""
        if self.classUri == schema.CLIP:  # for a clip, use the program reference
            if DAAN_PROGRAM_ID in metadata:
                self.graph.add((self.itemNode,
                                URIRef(schema.IS_PART_OF_PROGRAM),
                                URIRef(get_uri(daan_id=metadata[DAAN_PROGRAM_ID])))
                               )
            elif DAAN_PAYLOAD in metadata and DAAN_PROGRAM_ID in metadata[
                DAAN_PAYLOAD]:  # this is the case in the backbone json
                self.graph.add((self.itemNode,
                                URIRef(schema.IS_PART_OF_PROGRAM),
                                URIRef(get_uri(daan_id=metadata[DAAN_PAYLOAD][DAAN_PROGRAM_ID])))
                )
        elif DAAN_PARENT in metadata and metadata[DAAN_PARENT] and DAAN_PARENT in metadata[DAAN_PARENT]:
            # for other
            if type(metadata[DAAN_PARENT][DAAN_PARENT]) is list:
                parents = metadata[DAAN_PARENT][DAAN_PARENT]
            else:  # convert it to a list for consistent handling
                parents = [metadata[DAAN_PARENT][DAAN_PARENT]]

            for parent in parents:
                # for each parent, link it with the correct relationship given the types
                if self.classUri == schema.CARRIER:  # link carriers as children
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_CARRIER_OF),
                                    URIRef(get_uri(cat_type='carrier', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_PART_OF_SERIES),
                                    URIRef(get_uri(cat_type='series', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_PART_OF_SEASON),
                                    URIRef(get_uri(cat_type='season', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_PART_OF_PROGRAM),
                                    URIRef(get_uri(daan_id=parent[DAAN_PARENT_ID]))
                                    ))
        elif type(metadata[DAAN_PARENT]) is list:  # this is the case for the backbone json
            for parent in metadata[DAAN_PARENT]:
                # for each parent, link it with the correct relationship given the types
                if self.classUri == schema.CARRIER:  # link carriers as children
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_CARRIER_OF),
                                    URIRef(get_uri(cat_type='carrier', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_PART_OF_SERIES),
                                    URIRef(get_uri(cat_type='series', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_PART_OF_SEASON),
                                    URIRef(get_uri(cat_type='season', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
                    self.graph.add((self.itemNode,
                                    URIRef(schema.IS_PART_OF_PROGRAM),
                                    URIRef(get_uri(daan_id=parent[DAAN_PARENT_ID]))
                                    ))

        return

    def serialize(self, return_format):
        """ Serialize graph data to requested format."""
        try:
            return self.graph.serialize(
                format=return_format,
                context=dict(self.graph.namespaces()),
                auto_compact=True
            )
        except PluginException as e:
            print(e)
        except Exception as e:
            print('serializeGraph => ')
            print(e)
