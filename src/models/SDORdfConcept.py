import models.SDORdfModel as SDORdfModel
from models.DAANJsonModel import DAAN_PROGRAM_ID, DAAN_PARENT, DAAN_PARENT_ID, DAAN_PARENT_TYPE, DAAN_PAYLOAD, \
    ObjectType
from rdflib.namespace import RDF, RDFS, SKOS, Namespace
from rdflib import URIRef, Literal, BNode
from util.APIUtil import APIUtil
from models.BaseRdfConcept import BaseRdfConcept
from cache import cache
from importer.DAANSchemaImporter import DAANSchemaImporter


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

        # self.graph.namespace_manager.bind(self._model.SCHEMA_DOT_ORG_PREFIX,
        self.graph.namespace_manager.bind('@vocab',
                                          Namespace(self._model.SCHEMA_DOT_ORG_NAMESPACE))
        # create a node for the record
        self.itemNode = URIRef(self.get_uri(concept_type, metadata["id"]))

        # get the RDF class URI for this type
        self.classUri = self._model.CLASS_URIS_FOR_DAAN_LEVELS[concept_type]

        # add the type
        self.graph.add((self.itemNode, RDF.type, URIRef(self.classUri)))

        # add a GPP landing page for the item
        self.landing_page = self.get_gpp_link(concept_type, metadata["id"])
        if self.landing_page is not None:
            self.graph.add((self.itemNode, URIRef(self._model.URL), URIRef(self.landing_page)))

        # convert the record payload to RDF
        self.__payload_to_rdf(metadata["payload"], self.itemNode, self.classUri)

        # create RDF relations with the parents of the record
        self.__parent_to_rdf(metadata)

    @cache.cached(timeout=0, key_prefix='sdo_scheme')
    def get_scheme(self):
        """ Returns a schema instance."""
        # FIXME this does not work yet for the SDO schema (see the DAANSchemaImporter)
        return DAANSchemaImporter(self.profile["schema"], self.profile["mapping"])

    def __create_skos_concept(self, used_path, payload, concept_label, property_description):
        """Searches in the concept_metadata for a thesaurus concept. If one is found, creates a node for it and
        adds the concept_label as its label, then links it to the parent_node, using the property_uri, and
        sets its type to the range and additionalType values in the property_description"""
        skos_concept_node = None

        # look one step higher to get the ID of the thesaurus item
        concept_metadata = []
        if "," in used_path:
            class_path = ",".join(used_path.split(",")[:-1])
            concept_metadata = self._get_metadata_value(payload, class_path)

            # the value could be a list, so make sure it always is so can treat everything the same way
            if type(concept_metadata) is not list:
                concept_metadata = [concept_metadata]

        for concept in concept_metadata:
            if "origin" in concept and "value" in concept and "resolved_value" in concept:
                if concept["resolved_value"] == concept_label:
                    # we have found the right thesaurus concept and can use the value to generate the URI
                    if property_description["range"] in self._model.NON_GTAA_TYPES:
                        skos_concept_node = URIRef(self._model.NON_GTAA_NAMESPACE + concept["value"])
                    else:
                        skos_concept_node = URIRef(self._model.GTAA_NAMESPACE + concept["value"])

                    # type is set to Person or Organization depending on the property range
                    # additionalType is set to SKOS concept
                    self.graph.add((skos_concept_node, RDF.type, URIRef(property_description["range"])))
                    self.graph.add((skos_concept_node, URIRef(self._model.ADDITIONAL_TYPE), SKOS.Concept))

                    self.graph.add((skos_concept_node, SKOS.prefLabel, Literal(concept_label, lang="nl")))
                    break

        return skos_concept_node

    def __payload_to_rdf(self, payload, parent_node, class_uri):
        """ Converts the metadata described in payload (json) to RDF, and attaches it to the parentNode
        (e.g. the parentNode can be the identifier node for a program, and the payload the metadata describing
        that program). Calls itself recursively to handle any classes in the metadata, e.g. the publication
        belonging to a program.
        Uses the classUri of the parent node to select the right information from classes for the conversion.
        :param payload: a JSON string of metadata
        :param parent_node: an ID of the parent node (e.g. like a 'scene description' has a 'program' as parent)
        :param class_uri: the class URI for the parent node

        :returns: the result in graph
        """
        # Select the relevant properties for this type of parent using the classUri
        properties = self._classes[class_uri]["properties"]

        # retrieve metadata for each relevant property
        for property_uri, property_description in properties.items():

            # try each possible path for the property until find some metadata
            property_payload = []
            used_paths = []
            for path in property_description["paths"]:
                new_payload = self._get_metadata_value(payload, path)
                if new_payload:
                    if type(new_payload) is list:
                        for payload_item in new_payload:
                            property_payload.append(payload_item)
                            used_paths.append(path)
                    else:
                        property_payload.append(new_payload)
                        used_paths.append(path)

            # for each item in the metadata list
            i = 0
            for new_payload_item in property_payload:
                # if range of property is simple data type, just link it to the parent using the property
                used_path = used_paths[i]
                i += 1
                if property_uri == self._model.CONDITIONS_OF_ACCESS:
                    # we are generating the access conditions, for which we want to use the showbrowse property to
                    # determine the correct message
                    access_text = "Media is not available for viewing/listening online"
                    if new_payload_item.lower() == "true":
                        access_text = "View/listen to media online at the item's URL: True"

                    self.graph.add((parent_node, URIRef(property_uri), Literal(access_text, datatype=property_description[
                        "range"])))

                elif property_description["range"] in self._model.XSD_TYPES:
                    self.graph.add((parent_node, URIRef(property_uri), Literal(new_payload_item, datatype=property_description[
                        "range"])))  # add the new payload as the value
                elif property_description["range"] in self._model.ROLE_TYPES or property_uri == self._model.MENTIONS:
                    # In these cases, we have a person or organisation linked via a role,
                    # so we first need to create a node for the  person or organisation
                    # then we need to create a node for the role
                    # then point from that node to the node for the Person or organisation

                    # try to create a SKOS concept node
                    concept_node = self.__create_skos_concept(used_path, payload, new_payload_item, property_description)

                    if concept_node is None:
                        # we couldn't find a skos concept so we only have a label, so we create a blank node
                        concept_node = BNode()
                        # set the rdfs label of the concept node to be the DAAN payload item
                        self.graph.add((concept_node, RDFS.label, Literal(new_payload_item, lang="nl")))

                    # create a blank node for the role
                    role_node = BNode()
                    # link the role node to the parent node
                    self.graph.add((parent_node, URIRef(property_uri), role_node))

                    # link the concept node to the role node
                    self.graph.add((role_node, URIRef(property_uri), concept_node))

                elif "additionalType" in property_description and property_description[
                    "additionalType"] == str(SKOS.Concept):
                    # In these cases, we have a class as range, but only a simple value in DAAN, as we want
                    # to model a label from DAAN with a skos:Concept in the RDF
                    # create a node for the skos concept

                    # try to create a SKOS concept node
                    concept_node = self.__create_skos_concept(used_path, payload, new_payload_item,
                                                              property_description)

                    if concept_node is None:
                        # we couldn't find a skos concept so we only have a label, so we create a blank node
                        concept_node = BNode()
                        # set the rdfs label of the concept node to be the DAAN payload item
                        self.graph.add((concept_node, RDFS.label, Literal(new_payload_item, lang="nl")))

                    self.graph.add((parent_node, URIRef(property_uri), concept_node))  # link it to the parent

                else:
                    # we have a class as range
                    # create a blank node for the class ID, and a triple to set the type of the class
                    blank_node = BNode()
                    self.graph.add((blank_node, RDF.type, URIRef(property_description["range"])))
                    self.graph.add((parent_node, URIRef(property_uri), blank_node))  # link it to the parent
                    # and call the function again to handle the properties for the class
                    self.__payload_to_rdf(new_payload_item, blank_node, property_description["range"])

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
