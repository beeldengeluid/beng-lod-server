import models.SDORdfModel as SDORdfModel
from models.DAANJsonModel import DAAN_PROGRAM_ID, DAAN_PARENT, DAAN_PARENT_ID, DAAN_PARENT_TYPE, DAAN_PAYLOAD, \
    ObjectType
from rdflib.namespace import RDF, RDFS, SKOS, Namespace
from rdflib import URIRef, Literal, BNode
from util.APIUtil import APIUtil
from models.BaseRdfConcept import BaseRdfConcept
from cache import cache
from apis.lod.DAANSchemaImporter import DAANSchemaImporter


class SDORdfConcept(BaseRdfConcept):
    """ Class to represent an NISV catalog object in RDF.
        It uses functions to create the RDF in a graph using the JSON payload from the Direct Access Metadata API.

    """

    def __init__(self, metadata, concept_type, profile):
        super().__init__(profile, model=SDORdfModel)
        self._schema = self.get_scheme()
        self._classes = self._schema.get_classes()

        err_msg = 'Error while loading the schema classes and properties'
        assert self._classes is not None, APIUtil.raiseDescriptiveValueError('internal_server_error', err_msg)

        self.graph.namespace_manager.bind(self._model.SCHEMA_DOT_ORG_PREFIX,
                                          Namespace(self._model.SCHEMA_DOT_ORG_NAMESPACE))
        # create a node for the record
        self.itemNode = URIRef(self.get_uri(concept_type, metadata["id"]))

        # get the RDF class URI for this type
        self.classUri = self._model.CLASS_URIS_FOR_DAAN_LEVELS[concept_type]

        # add the type
        self.graph.add((self.itemNode, RDF.type, URIRef(self.classUri)))

        # convert the record payload to RDF
        self.__payload_to_rdf(metadata["payload"], self.itemNode, self.classUri)

        # create RDF relations with the parents of the record
        self.__parent_to_rdf(metadata)

    @cache.cached(timeout=0, key_prefix='sdo_scheme')
    def get_scheme(self):
        """ Returns a schema instance."""
        #FIXME this does not work yet for the SDO schema (see the DAANSchemaImporter)
        return DAANSchemaImporter(self.profile["schema"], self.profile["mapping"])

    def __payload_to_rdf(self, payload, parent_node, class_uri):
        """ Converts the metadata described in payload (json) to RDF, and attaches it to the parentNode
        (e.g. the parentNode can be the identifier node for a program, and the payload the metadata describing
        that program.). Calls itself recursively to handle any classes in the metadata, e.g. the publication
        belonging to a program.
        Uses the classUri of the parent node to select the right information from  classes for the conversion.
        Returns the result in graph
        """
        # Select the relevant properties for this type of parent using the classUri
        properties = self._classes[class_uri]["properties"]

        # retrieve metadata for each relevant property
        for uri, rdfProperty in properties.items():

            # try each possible path for the property until find some metadata
            new_payload = None
            used_path = None
            for path in rdfProperty["paths"]:
                new_payload = self._get_metadata_value(payload, path)
                used_path = path
                if new_payload:
                    break

            # if we found metadata for this property
            if new_payload:
                if type(new_payload) is not list:
                    new_payload = [new_payload]  # we can have a list of metadata, so make sure it is always
                # a list for consistent handling

                # for each item in the metadata list
                for newPayloadItem in new_payload:
                    # if range of property is simple data type, just link it to the parent using the property
                    if rdfProperty["range"] in self._model.XSD_TYPES:
                        self.graph.add((parent_node, URIRef(uri), Literal(newPayloadItem, datatype=rdfProperty[
                            "range"])))  # add the new payload as the value
                    elif rdfProperty[
                        "rangeSuperClass"] == str(SKOS.Concept):
                        # In these cases, we have a class as range, but only a simple value in DAAN, as we want
                        # to model a label from DAAN with a skos:Concept in the RDF
                        # create a node for the skos concept

                        # look one step higher to be able to get to the ID of a thesaurus item
                        concept_metadata = []
                        if used_path is not None and "," in used_path:
                            class_path = ",".join(used_path.split(",")[:-1])
                            concept_metadata = self._get_metadata_value(payload, class_path)

                            # the value could be a list, so make sure it always is so can treat everything the same way
                            if type(concept_metadata) is not list:
                                concept_metadata = [concept_metadata]

                        concept_node = None
                        skos_concept = None
                        for concept in concept_metadata:
                            if "origin" in concept and "value" in concept and "resolved_value" in concept:
                                if concept["resolved_value"] == newPayloadItem:
                                    # we have a thesaurus concept and can use the value to generate the URI
                                    if rdfProperty["range"] in self._model.NON_GTAA_TYPES:
                                        concept_node = URIRef(self._model.NON_GTAA_NAMESPACE + concept["value"])
                                    else:
                                        concept_node = URIRef(self._model.GTAA_NAMESPACE + concept["value"])
                                skos_concept = True
                        if not concept_node:
                            # we only have a label, so we create a blank node
                            concept_node = BNode()
                            skos_concept = False

                        self.graph.add((concept_node, RDF.type, URIRef(rdfProperty["range"])))
                        self.graph.add((parent_node, URIRef(uri), concept_node))  # link it to the parent

                        if skos_concept is True:
                            # set the pref label of the concept node to be the DAAN payload item
                            self.graph.add((concept_node, SKOS.prefLabel, Literal(newPayloadItem, lang="nl")))
                        else:
                            # set the rdfs label of the concept node to be the DAAN payload item
                            self.graph.add((concept_node, RDFS.label, Literal(newPayloadItem, lang="nl")))
                    else:
                        # we have a class as range
                        # create a blank node for the class ID, and a triple to set the type of the class
                        blank_node = BNode()
                        self.graph.add((blank_node, RDF.type, URIRef(rdfProperty["range"])))
                        self.graph.add((parent_node, URIRef(uri), blank_node))  # link it to the parent
                        # and call the function again to handle the properties for the class
                        self.__payload_to_rdf(newPayloadItem, blank_node, rdfProperty["range"])

        return

    def __parent_to_rdf(self, metadata):
        """Depending on the type of the child (e.g. program) retrieve the information about its
        parents from the metadata, link the child to the parents, and return the new instances and
        properties in the graph"""
        if self.classUri == self._model.CLIP:  # for a clip, use the program reference
            if DAAN_PROGRAM_ID in metadata:
                self.graph.add(
                    (URIRef(self.get_uri(daan_id=metadata[DAAN_PROGRAM_ID])),
                     URIRef(self._model.HAS_CLIP),
                     self.itemNode)
                )
            elif DAAN_PAYLOAD in metadata and DAAN_PROGRAM_ID in metadata[
                DAAN_PAYLOAD]:  # this is the case in the backbone json
                self.graph.add(
                    (URIRef(self.get_uri(daan_id=metadata[DAAN_PAYLOAD][DAAN_PROGRAM_ID])),
                     URIRef(self._model.HAS_CLIP),
                     self.itemNode)
                )
        elif DAAN_PARENT in metadata and metadata[DAAN_PARENT] and DAAN_PARENT in metadata[DAAN_PARENT]:
            # for other
            if type(metadata[DAAN_PARENT][DAAN_PARENT]) is list:
                parents = metadata[DAAN_PARENT][DAAN_PARENT]
            else:  # convert it to a list for consistent handling
                parents = [metadata[DAAN_PARENT][DAAN_PARENT]]

            for parent in parents:
                # for each parent, link it with the correct relationship given the types
                if self.classUri == self._model.CARRIER:  # link carriers as children
                    self.graph.add((self.itemNode,
                                    URIRef(self._model.IS_CARRIER_OF),
                                    URIRef(self.get_uri(cat_type='carrier', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
                    self.graph.add((self.itemNode,
                                    URIRef(self._model.IS_PART_OF_SERIES),
                                    URIRef(self.get_uri(cat_type='series', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
                    self.graph.add((self.itemNode,
                                    URIRef(self._model.IS_PART_OF_SEASON),
                                    URIRef(self.get_uri(cat_type='season', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
                    self.graph.add((URIRef(self.get_uri(daan_id=parent[DAAN_PARENT_ID])),
                                    URIRef(self._model.HAS_CLIP),
                                    self.itemNode
                                    ))
        elif type(metadata[DAAN_PARENT]) is list:  # this is the case for the backbone json
            for parent in metadata[DAAN_PARENT]:
                # for each parent, link it with the correct relationship given the types
                if self.classUri == self._model.CARRIER:  # link carriers as children
                    self.graph.add((self.itemNode,
                                    URIRef(self._model.IS_CARRIER_OF),
                                    URIRef(self.get_uri(cat_type='carrier', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
                    self.graph.add((self.itemNode,
                                    URIRef(self._model.IS_PART_OF_SERIES),
                                    URIRef(self.get_uri(cat_type='series', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
                    self.graph.add((self.itemNode,
                                    URIRef(self._model.IS_PART_OF_SEASON),
                                    URIRef(self.get_uri(cat_type='season', daan_id=parent[DAAN_PARENT_ID]))
                                    ))
                elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
                    self.graph.add((URIRef(self.get_uri(daan_id=parent[DAAN_PARENT_ID])),
                                    URIRef(self._model.HAS_CLIP),
                                    self.itemNode
                                    ))
        return
