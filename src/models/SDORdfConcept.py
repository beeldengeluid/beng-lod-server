import json
import models.SDORdfModel as SDORdfModel
from models.DAANJsonModel import (
    DAAN_PROGRAM_ID,
    DAAN_PARENT,
    DAAN_PARENT_ID,
    DAAN_PARENT_TYPE,
    DAAN_PAYLOAD,
    ObjectType,
)
from rdflib.namespace import RDF, RDFS, SKOS, Namespace, SDO
from rdflib import URIRef, Literal, BNode
from util.APIUtil import APIUtil
from models.BaseRdfConcept import BaseRdfConcept
from importer.DAANSchemaImporter import DAANSchemaImporter


class SDORdfConcept(BaseRdfConcept):
    """Class to represent an NISV catalog object with RDF using SDO schema.
    The class can be instantiated from the JSON payload provided by
    the NISV Direct Access Metadata API.

    """

    def __init__(self, metadata, concept_type, profile, logger, cache):
        super().__init__(profile, logger, model=SDORdfModel)
        self.cache = cache
        self._schema = self.get_scheme()
        self._classes = self._schema.get_classes()
        self.information_dictionary = self.get_information_directory()

        err_msg = "Error while loading the schema classes and properties"
        assert self._classes is not None, APIUtil.raiseDescriptiveValueError(
            "internal_server_error", err_msg
        )

        self.graph.namespace_manager.bind(
            "sdo", SDO._NS
        )
        # create a node for the record
        self.itemNode = URIRef(self.get_uri(concept_type, metadata["id"]))

        # get the RDF class URI for this type
        self.classUri = self._model.CLASS_URIS_FOR_DAAN_LEVELS[concept_type]

        # add the type
        self.graph.add((self.itemNode, RDF.type, URIRef(self.classUri)))

        # add a GPP landing page for the item
        self.landing_page = self.get_gpp_link(metadata, concept_type, metadata["id"])
        if self.landing_page is not None:
            self.graph.add(
                (self.itemNode, URIRef(self._model.URL), URIRef(self.landing_page))
            )

        # add links from Open Beelden, via media objects
        links, website = self.get_open_beelden_information(metadata["id"])
        if links is not None:
            for link in links:
                self.__add_media_object(link)
        if website is not None:
            self.graph.add(
                (
                    self.itemNode,
                    URIRef(self._model.IS_MAIN_ENTITY_OF_PAGE),
                    URIRef(website),
                )
            )

        # add the publisher triple
        self.graph.add(
            (self.itemNode, SDORdfModel.HAS_PUBLISHER, URIRef(self._model.URI_NISV_ORGANISATION))
        )

        # convert the record payload to RDF
        self.__payload_to_rdf(metadata["payload"], self.itemNode, self.classUri)

        # create RDF relations with the parents of the record
        self.__parent_to_rdf(metadata)

    # TODO: make a module for rights
    def rights_to_license_uri(self, payload=None):  # noqa: C901 #TODO
        """Analyse the metadata, return a proper CC license.
        This is an implementation of the rules in the beng-lod wiki page:
        https://github.com/beeldengeluid/beng-lod-server/wiki/Rights-and-licenses-for-NISV-open-data
        :param payload: JSON metadata.
        :returns: CC license or None if param not given or license not determined.
        """
        if payload is None:
            return None

        # get the necessary metadata values to determine the right statuses
        rights_license = self._get_metadata_value(payload, "nisv.rightslicense")
        status = rights_license.get("resolved_value")
        iprcombined = self._get_metadata_value(payload, "nisv.iprcombined")
        iprc = (
            iprcombined.get("resolved_value") if isinstance(iprcombined, dict) else None
        )
        ethicalprivatecombined = self._get_metadata_value(
            payload, "nisv.ethicalprivatecombined"
        )
        epc = (
            ethicalprivatecombined.get("resolved_value")
            if isinstance(ethicalprivatecombined, dict)
            else None
        )
        collection_group_list = self._get_metadata_value(
            payload, "nisv.collectionsgroup"
        )
        collection_group = ""
        for collectionsgroup in collection_group_list:
            collection_group_dir = (
                collectionsgroup.get("collectionsgroup.dir")
                if isinstance(collectionsgroup, dict)
                else None
            )
            collection_group = (
                collection_group_dir.get("resolved_value")
                if isinstance(collection_group_dir, dict)
                else None
            )

        license_condition = self._get_metadata_value(payload, "nisv.licensecondition")
        cc_value = (
            license_condition.get("resolved_value")
            if isinstance(license_condition, dict)
            else None
        )

        # BLOCKED
        if (
            status == "Blocked"
            and iprc is None
            and collection_group
            in [
                "Commerciële omroepen",
                "Publieke omroepen",
                "Regionale omroepen",
                "Handelsplaten",
            ]
        ):
            return self._model.RS_IN_COPYRIGHT

        if (
            status == "Blocked"
            and iprc is None
            and collection_group in ["Beeld en Geluid", "Overige", ""]
        ):
            return self._model.RS_COPYRIGHT_NOT_EVALUATED
        # default
        if status == "Blocked":
            raise NotImplementedError

        # REQUIRED LICENSE
        if (
            status == "Required license"
            and epc == ""
            and collection_group
            in [
                "Commerciële omroepen",
                "Publieke omroepen",
                "Regionale omroepen",
                "Handelsplaten",
            ]
        ):
            return self._model.RS_IN_COPYRIGHT

        if (
            status == "Required license"
            and epc == "Required License"
            and iprc == "Public domain"
        ):
            return self._model.RS_OTHER_LEGAL_RESTRICTIONS

        if status == "Required license" and epc == "Required license" and iprc == "":
            return self._model.RS_COPYRIGHT_NOT_EVALUATED

        # LICENSE CHECK
        if status == "License check" and collection_group in [
            "Commerciële omroepen",
            "Publieke omroepen",
            "Regionale omroepen",
            "Handelsplaten",
        ]:
            return self._model.RS_IN_COPYRIGHT

        if status == "License check" and collection_group in ["Tweede Kamer"]:
            return self._model.TK_AUDIOVISUAL_LICENSE

        if status == "License check" and collection_group in [
            "Beeld en Geluid",
            "Overige",
            "",
        ]:
            return self._model.RS_COPYRIGHT_NOT_EVALUATED

        # LICENSE FREE - ORPHHAN STATUS
        if status == "License free - Orphan status":
            # NISV doesn't have any orphan works, so if we see this status return 'not evaluated'
            return self._model.RS_COPYRIGHT_NOT_EVALUATED

        # LICENSE FREE - PUBLIC DOMAIN
        if status == "License free - Public domain" and epc == "Required License":
            return self._model.RS_OTHER_LEGAL_RESTRICTIONS

        if status == "License free - Public domain" and epc == "Assessed, not blocked":
            return self._model.CC_PDM

        # RELEASED and LICENSE FREE - RELEASED BY RIGHTSHOLDER
        # TODO: check the rightsholder
        if (
            status in ["License free - Released by rightsholder", "Released"]
            and iprc == "Public domain"
            and epc == "Assessed, not blocked"
        ):
            return self._model.CC_PDM

        if (
            status in ["License free - Released by rightsholder", "Released"]
            and iprc == "Released under license"
            and epc == "Assessed, not blocked"
            and cc_value == "CC-BY"
        ):
            return self._model.CC_BY

        if (
            status in ["License free - Released by rightsholder", "Released"]
            and iprc == "Released under license"
            and epc == "Assessed, not blocked"
            and cc_value == "CC-BY-SA"
        ):
            return self._model.CC_BY_SA

        # DEFAULT, not a valid license available
        raise NotImplementedError

    # use a simple in-memory cache
    def get_scheme(self, cache_key="sdo_scheme"):
        if cache_key in self.cache:
            self.logger.debug("GOT THE sdo_scheme FROM CACHE")
            return self.cache[cache_key]
        else:
            self.logger.debug("NO sdo_scheme FOUND IN CACHE")
            sdo_scheme = DAANSchemaImporter(
                self.profile["schema"], self.profile["mapping"], self.logger
            )
            self.cache[cache_key] = sdo_scheme
            return sdo_scheme

    # use a simple in-memory cache
    def get_information_directory(self, cache_key="ob_links"):
        if cache_key in self.cache:
            self.logger.debug("GOT THE ob_links FROM CACHE")
            return self.cache[cache_key]
        else:
            self.logger.debug("NO ob_links FOUND IN CACHE")
            with open(self.profile["ob_links"]) as ob_information_file:
                ob_data = json.load(ob_information_file)
                self.cache[cache_key] = ob_data
                return ob_data

    def get_open_beelden_information(self, item_id):
        links = None
        website = None
        if item_id in self.information_dictionary:
            links = self.information_dictionary[item_id]["content_links"]
            website = self.information_dictionary[item_id]["website"]
        return links, website

    def __add_media_object(self, content_url):
        """Adds a media object to the RDF item, and links it to the content_url via the media object"""

        # create a media object. NB: Do NOT use a DAAN ID as we use this function to model info from open beelden
        # items, which are not listed within DAAN but are derived from certain DAAN items.

        media_object_node = (
            BNode()
        )  # use a BNode to emphasize that this Media Object is not an entity in DAAN
        self.graph.add(
            (self.itemNode, URIRef(self._model.HAS_ASSOCIATED_MEDIA), media_object_node)
        )
        self.graph.add((media_object_node, RDF.type, URIRef(self._model.CARRIER)))
        self.graph.add(
            (
                media_object_node,
                URIRef(self._model.HAS_CONTENT_URL),
                URIRef(content_url),
            )
        )
        self.graph.add(
            (
                media_object_node,
                URIRef(self._model.HAS_ENCODING_FORMAT),
                Literal("video/mp4"),
            )
        )

    def __add_material_type_object(self, content_url=None, material_type=None):
        """Given the material type, a media object is added to the RDF item. If the content_url is given,
        it is linked to the media object.
        :param content_url: pointer to the media that represents the creative work.
        :param material_type: DAAN property for the sort of media object (audio, video, photo, paper, object, other).
        This function handles (audio, video, photo), because they get an associatedMedia property.
        """
        if material_type is not None:
            media_object_node = (
                BNode()
            )  # use a BNode to emphasize that this Media Object is not an entity in DAAN
            self.graph.add(
                (
                    self.itemNode,
                    URIRef(self._model.HAS_ASSOCIATED_MEDIA),
                    media_object_node,
                )
            )

            if material_type == "audio":
                self.graph.add((media_object_node, RDF.type, URIRef(self._model.AUDIO)))
                self.graph.add(
                    (
                        media_object_node,
                        URIRef(self._model.HAS_ENCODING_FORMAT),
                        Literal("audio/mp3"),
                    )
                )
            elif material_type == "video":
                self.graph.add((media_object_node, RDF.type, URIRef(self._model.VIDEO)))
                self.graph.add(
                    (
                        media_object_node,
                        URIRef(self._model.HAS_ENCODING_FORMAT),
                        Literal("video/mp4"),
                    )
                )
            elif material_type == "photo":
                self.graph.add((media_object_node, RDF.type, URIRef(self._model.PHOTO)))
                self.graph.add(
                    (
                        media_object_node,
                        URIRef(self._model.HAS_ENCODING_FORMAT),
                        Literal("image/jpeg"),
                    )
                )

            if content_url is not None:
                self.graph.add(
                    (
                        media_object_node,
                        URIRef(self._model.HAS_CONTENT_URL),
                        URIRef(content_url),
                    )
                )

    def __create_skos_concept(
        self, used_path, payload, concept_label, property_description
    ):
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
            if (
                "origin" in concept
                and "value" in concept
                and "resolved_value" in concept
            ):
                if concept["resolved_value"] == concept_label:
                    # we have found the right thesaurus concept and can use the value to generate the URI
                    skos_concept_node = URIRef(
                        self._model.GTAA_NAMESPACE + concept["value"]
                    )

                    # type is set to Person or Organization depending on the property range
                    # additionalType is set to SKOS concept
                    self.graph.add(
                        (
                            skos_concept_node,
                            RDF.type,
                            URIRef(property_description["range"]),
                        )
                    )
                    self.graph.add(
                        (
                            skos_concept_node,
                            URIRef(self._model.ADDITIONAL_TYPE),
                            SKOS.Concept,
                        )
                    )

                    self.graph.add(
                        (
                            skos_concept_node,
                            SKOS.prefLabel,
                            Literal(concept_label, lang="nl"),
                        )
                    )
                    break

        return skos_concept_node

    def __payload_to_rdf(self, payload, parent_node, class_uri):  # noqa: C901 #TODO
        """Converts the metadata described in payload (json) to RDF, and attaches it to the parentNode
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
        for property_uri_string, property_description in properties.items():
            property_uri = URIRef(property_uri_string)
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

                # do something with the material type
                if property_uri == self._model.HAS_MATERIAL_TYPE:
                    try:
                        media_material = new_payload_item.lower()
                        if media_material in ("audio", "video", "photo"):
                            # add the associatedMedia
                            self.__add_material_type_object(
                                content_url=None, material_type=media_material
                            )
                        elif media_material in ("paper", "object", "other"):
                            # add material property. Only 'paper' is really a physical substance, but add anyway...
                            self.graph.add(
                                (
                                    parent_node,
                                    URIRef(property_uri),
                                    Literal(media_material),
                                )
                            )
                    except NotImplementedError as e:
                        print(f"NotImplementedError: {str(e)}")

                elif property_uri == self._model.LICENSE:
                    try:
                        license_url = self.rights_to_license_uri(payload)
                        if license_url is not None:
                            # add the URI for the rights statement or license
                            self.graph.add(
                                (parent_node, URIRef(property_uri), URIRef(license_url))
                            )
                    except NotImplementedError as e:
                        print(str(e))

                elif property_uri == self._model.CONDITIONS_OF_ACCESS:
                    # we are generating the access conditions, for which we want to use the showbrowse property to
                    # determine the correct message
                    access_text = "Media is not available for viewing/listening online"
                    if new_payload_item.lower() == "true":
                        access_text = (
                            "View/listen to media online at the item's URL: True"
                        )

                    self.graph.add(
                        (
                            parent_node,
                            URIRef(property_uri),
                            Literal(
                                access_text, datatype=property_description["range"]
                            ),
                        )
                    )

                elif property_description["range"] in self._model.XSD_TYPES:
                    # add the new payload as the value
                    self.graph.add(
                        (
                            parent_node,
                            URIRef(property_uri),
                            Literal(
                                new_payload_item, datatype=property_description["range"]
                            ),
                        )
                    )
                elif (
                    property_description["range"] in self._model.ROLE_TYPES
                    or property_uri == self._model.MENTIONS
                ):
                    # In these cases, we have a person or organisation linked via a role,
                    # so we first need to create a node for the  person or organisation
                    # then we need to create a node for the role
                    # then point from that node to the node for the Person or organisation

                    # try to create a SKOS concept node
                    concept_node = self.__create_skos_concept(
                        used_path, payload, new_payload_item, property_description
                    )

                    if concept_node is None:
                        # we couldn't find a skos concept so we only have a label, so we create a blank node
                        concept_node = BNode()
                        # set the rdfs label of the concept node to be the DAAN payload item
                        self.graph.add(
                            (
                                concept_node,
                                RDFS.label,
                                Literal(new_payload_item, lang="nl"),
                            )
                        )

                    # create a blank node for the role
                    role_node = BNode()
                    # link the role node to the parent node
                    self.graph.add((parent_node, URIRef(property_uri), role_node))

                    # add the appropriate role type for the property.
                    if URIRef(property_uri) in SDORdfModel.ASSOCIATED_ROLES_FOR_PROPERTIES:
                        self.graph.add((role_node, RDF.type, SDORdfModel.ASSOCIATED_ROLES_FOR_PROPERTIES[URIRef(property_uri)]))

                    # link the concept node to the role node
                    self.graph.add((role_node, URIRef(property_uri), concept_node))

                elif "additionalType" in property_description and property_description[
                    "additionalType"
                ] == str(SKOS.Concept):
                    # In these cases, we have a class as range, but only a simple value in DAAN, as we want
                    # to model a label from DAAN with a skos:Concept in the RDF
                    # create a node for the skos concept

                    # try to create a SKOS concept node
                    concept_node = self.__create_skos_concept(
                        used_path, payload, new_payload_item, property_description
                    )

                    if concept_node is None:
                        # we couldn't find a skos concept so we only have a label, so we create a blank node
                        concept_node = BNode()
                        # set the rdfs label of the concept node to be the DAAN payload item
                        self.graph.add(
                            (
                                concept_node,
                                RDFS.label,
                                Literal(new_payload_item, lang="nl"),
                            )
                        )

                    # create a blank node for the role
                    role_node = BNode()
                    # link the role node to the parent node
                    self.graph.add((parent_node, URIRef(property_uri), role_node))

                    # add the appropriate role type for the property.
                    if URIRef(property_uri) in SDORdfModel.ASSOCIATED_ROLES_FOR_PROPERTIES:
                        self.graph.add((role_node, RDF.type, SDORdfModel.ASSOCIATED_ROLES_FOR_PROPERTIES[URIRef(property_uri)]))

                    # link the concept node to the role node
                    self.graph.add((role_node, URIRef(property_uri), concept_node))

                else:
                    # we have a class as range
                    # create a blank node for the class ID, and a triple to set the type of the class
                    blank_node = BNode()
                    self.graph.add(
                        (blank_node, RDF.type, URIRef(property_description["range"]))
                    )
                    self.graph.add(
                        (parent_node, URIRef(property_uri), blank_node)
                    )  # link it to the parent
                    # and call the function again to handle the properties for the class
                    self.__payload_to_rdf(
                        new_payload_item, blank_node, property_description["range"]
                    )

        return

    def __parent_to_rdf(self, metadata):  # noqa: C901 #TODO
        """Depending on the type of the child (e.g. program) retrieve the information about its
        parents from the metadata, link the child to the parents, and return the new instances and
        properties in the graph"""
        if self.classUri == self._model.CLIP:  # for a clip, use the program reference
            if DAAN_PROGRAM_ID in metadata:
                self.graph.add(
                    (
                        URIRef(self.get_uri(daan_id=metadata[DAAN_PROGRAM_ID])),
                        URIRef(self._model.HAS_CLIP),
                        self.itemNode,
                    )
                )
            elif (
                DAAN_PAYLOAD in metadata and DAAN_PROGRAM_ID in metadata[DAAN_PAYLOAD]
            ):  # this is the case in the backbone json
                self.graph.add(
                    (
                        URIRef(
                            self.get_uri(
                                daan_id=metadata[DAAN_PAYLOAD][DAAN_PROGRAM_ID]
                            )
                        ),
                        URIRef(self._model.HAS_CLIP),
                        self.itemNode,
                    )
                )
        elif (
            DAAN_PARENT in metadata
            and metadata[DAAN_PARENT]
            and DAAN_PARENT in metadata[DAAN_PARENT]
        ):
            # for other
            if type(metadata[DAAN_PARENT][DAAN_PARENT]) is list:
                parents = metadata[DAAN_PARENT][DAAN_PARENT]
            else:  # convert it to a list for consistent handling
                parents = [metadata[DAAN_PARENT][DAAN_PARENT]]

            for parent in parents:
                # for each parent, link it with the correct relationship given the types
                if self.classUri == self._model.CARRIER:  # link carriers as children
                    self.graph.add(
                        (
                            self.itemNode,
                            URIRef(self._model.IS_CARRIER_OF),
                            URIRef(
                                self.get_uri(
                                    cat_type="carrier", daan_id=parent[DAAN_PARENT_ID]
                                )
                            ),
                        )
                    )
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
                    self.graph.add(
                        (
                            self.itemNode,
                            URIRef(self._model.IS_PART_OF_SERIES),
                            URIRef(
                                self.get_uri(
                                    cat_type="series", daan_id=parent[DAAN_PARENT_ID]
                                )
                            ),
                        )
                    )
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
                    self.graph.add(
                        (
                            self.itemNode,
                            URIRef(self._model.IS_PART_OF_SEASON),
                            URIRef(
                                self.get_uri(
                                    cat_type="season", daan_id=parent[DAAN_PARENT_ID]
                                )
                            ),
                        )
                    )
                elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
                    self.graph.add(
                        (
                            URIRef(self.get_uri(daan_id=parent[DAAN_PARENT_ID])),
                            URIRef(self._model.HAS_CLIP),
                            self.itemNode,
                        )
                    )
        elif (
            type(metadata[DAAN_PARENT]) is list
        ):  # this is the case for the backbone json
            for parent in metadata[DAAN_PARENT]:
                # for each parent, link it with the correct relationship given the types
                if self.classUri == self._model.CARRIER:  # link carriers as children
                    self.graph.add(
                        (
                            self.itemNode,
                            URIRef(self._model.IS_CARRIER_OF),
                            URIRef(
                                self.get_uri(
                                    cat_type="carrier", daan_id=parent[DAAN_PARENT_ID]
                                )
                            ),
                        )
                    )
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
                    self.graph.add(
                        (
                            self.itemNode,
                            URIRef(self._model.IS_PART_OF_SERIES),
                            URIRef(
                                self.get_uri(
                                    cat_type="series", daan_id=parent[DAAN_PARENT_ID]
                                )
                            ),
                        )
                    )
                elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
                    self.graph.add(
                        (
                            self.itemNode,
                            URIRef(self._model.IS_PART_OF_SEASON),
                            URIRef(
                                self.get_uri(
                                    cat_type="season", daan_id=parent[DAAN_PARENT_ID]
                                )
                            ),
                        )
                    )
                elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
                    self.graph.add(
                        (
                            URIRef(self.get_uri(daan_id=parent[DAAN_PARENT_ID])),
                            URIRef(self._model.HAS_CLIP),
                            self.itemNode,
                        )
                    )
        return
