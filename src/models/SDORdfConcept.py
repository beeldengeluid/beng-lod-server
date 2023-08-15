import csv
import csv
import json
import logging
import validators

from rdflib.namespace import RDF, RDFS, SKOS, SDO
from rdflib import URIRef, Literal, BNode
from typing import Dict, Optional

import logging
import validators

from rdflib.namespace import RDF, RDFS, SKOS, SDO
from rdflib import URIRef, Literal, BNode
from typing import Dict, Optional

import models.SDORdfModel as SDORdfModel

from importer.DAANSchemaImporter import DAANSchemaImporter
from models.BaseRdfConcept import BaseRdfConcept
from models.DAANJsonModel import (
    DAAN_PROGRAM_ID,
    DAAN_PARENT,
    DAAN_PARENT_ID,
    DAAN_PARENT_TYPE,
    DAAN_PAYLOAD,
    ObjectType,
)
from util.APIUtil import APIUtil
from util.role_util import parse_role_label, match_role

logger = logging.getLogger()


class SDORdfConcept(BaseRdfConcept):
    """Class to represent an NISV catalog object with RDF using SDO schema.
    The class can be instantiated from the JSON payload provided by
    the NISV Direct Access Metadata API.

    """

    def __init__(self, metadata, concept_type, profile, cache):
        super().__init__(profile, model=SDORdfModel)
        self.cache = cache
        self._schema = self.get_scheme()
        self._classes = self._schema.get_classes()
        self.open_beelden_matches = self.get_open_beelden_matches()

        err_msg = "Error while loading the schema classes and properties"
        assert self._classes is not None, APIUtil.raiseDescriptiveValueError(
            "internal_server_error", err_msg
        )

        self.graph.namespace_manager.bind("sdo", SDO._NS)
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

        # add the open beelden links if we have a match
        open_beelden_match = self.open_beelden_matches.get(metadata["id"])
        if open_beelden_match is not None:
            self.__add_open_beelden_links(open_beelden_match)

        # add the publisher triple
        self.graph.add(
            (
                self.itemNode,
                SDORdfModel.HAS_PUBLISHER,
                URIRef(self._model.URI_NISV_ORGANISATION),
            )
        )

        # convert the record payload to RDF
        if metadata.get("payload") is not None:
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
        rights_license = BaseRdfConcept._get_metadata_value(
            payload, "nisv.rightslicense"
        )
        status = rights_license.get("resolved_value")
        iprcombined = BaseRdfConcept._get_metadata_value(payload, "nisv.iprcombined")
        iprc = (
            iprcombined.get("resolved_value") if isinstance(iprcombined, dict) else None
        )
        ethicalprivatecombined = BaseRdfConcept._get_metadata_value(
            payload, "nisv.ethicalprivatecombined"
        )
        epc = (
            ethicalprivatecombined.get("resolved_value")
            if isinstance(ethicalprivatecombined, dict)
            else None
        )
        collection_group_list = BaseRdfConcept._get_metadata_value(
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

        license_condition = BaseRdfConcept._get_metadata_value(
            payload, "nisv.licensecondition"
        )
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
            logger.debug("GOT THE sdo_scheme FROM CACHE")
            return self.cache[cache_key]
        else:
            logger.debug("NO sdo_scheme FOUND IN CACHE")
            sdo_scheme = DAANSchemaImporter(
                self.profile["schema"], self.profile["mapping"]
            )
            self.cache[cache_key] = sdo_scheme
            return sdo_scheme

    # use a simple in-memory cache
    def get_open_beelden_matches(self, cache_key="ob_links"):
        if cache_key in self.cache:
            logger.debug("GOT THE ob_links FROM CACHE")
            return self.cache[cache_key]
        else:
            logger.debug("NO ob_links FOUND IN CACHE")
            with open(self.profile["ob_links"]) as ob_information_file:
                ob_data = json.load(ob_information_file)
                self.cache[cache_key] = ob_data
                return ob_data

    def get_matching_role_information(self, role_name: str):
        """Gets information about suitable roles based on the
        content of the role_name, which may contain multiple roles
        :param role_name - the value of the role name metadata field
        :returns a list of matching URIs and their labels and types"""
        role_strings = parse_role_label(role_name, ["/", ",", r"\+"])
        role_data = self.get_role_data()
        matched_roles = match_role(role_strings, role_data["groups"])
        role_information_list = []
        for matched_role in matched_roles:
            if role_data["mapping"][matched_role]["wikidata_identifier"]:
                role_information_list.append(
                    (
                        role_data["mapping"][matched_role]["wikidata_identifier"],
                        role_data["mapping"][matched_role]["wikidata_label"],
                        role_data["mapping"][matched_role]["wikidata_type"],
                    )
                )
            if role_data["mapping"][matched_role]["um_identifier"]:
                role_information_list.append(
                    (
                        role_data["mapping"][matched_role]["um_identifier"],
                        role_data["mapping"][matched_role]["um_label"],
                        role_data["mapping"][matched_role]["um_type"],
                    )
                )

        return role_information_list

    @staticmethod
    def create_role_groups(role_data: Dict[str, Dict[str, str]]):
        """Given the role data, create a list of role groups that contain
        the same basic role
        :param role_data a dict of the role_data, with role string as key,
        and as value a dict of the various identifiers and labels the role is mapped to
        :returns a list of lists for the group labels"""
        # get all single words
        base_roles = [role for role in role_data if " " not in role]
        role_groups = []

        # now get only base roles that aren't contained in another role
        simplest_base_roles = []
        for base_role in base_roles:
            simplest = True
            for other_base_role in base_roles:
                if other_base_role == base_role:
                    continue
                if other_base_role in base_role:
                    simplest = False
                    break
            if simplest:
                simplest_base_roles.append(base_role)

        # group all roles containing those words
        group_members = []
        for base_role in simplest_base_roles:
            role_group = [
                role for role in role_data if base_role.lower() in role.lower()
            ]
            group_members.extend(role_group)
            role_groups.append(role_group)

        return role_groups

    # use a simple in-memory cache
    def get_role_data(self, cache_key="roles"):
        if cache_key in self.cache:
            logger.debug("GOT THE roles FROM CACHE")
            return self.cache[cache_key]
        else:
            logger.debug("NO roles FOUND IN CACHE")
            if "roles" in self.profile:
                with open(self.profile["roles"]) as role_information_file:
                    csv_reader = csv.reader(role_information_file)
                    mapping = {}
                    header = True
                    for row in csv_reader:
                        if header:
                            header = False
                            continue
                        if row[0]:
                            mapping[row[0]] = {
                                "wikidata_identifier": row[1],
                                "wikidata_label": row[2],
                                "wikidata_type": row[3],
                                "um_identifier": row[4],
                                "um_label": row[5],
                                "um_type": row[6],
                            }
                    role_groups = SDORdfConcept.create_role_groups(mapping)

                    role_data = {"groups": role_groups, "mapping": mapping}

                    self.cache[cache_key] = role_data
                    return role_data
            else:
                return {}

    def __add_open_beelden_links(self, open_beelden_match):
        # add triple pointing to website
        website = open_beelden_match.get("website", "")
        if validators.url(website):
            self.graph.add(
                (
                    self.itemNode,
                    URIRef(self._model.IS_MAIN_ENTITY_OF_PAGE),
                    URIRef(website),
                )
            )

        # add content links
        content_links = open_beelden_match.get("content_links", [])
        for content_link in content_links:
            if validators.url(content_link):
                self.__add_media_object(content_link)

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

    @staticmethod
    def _get_role(used_path: str, payload: dict, subject_name: str) -> Optional[str]:
        """Searches in the concept_metadata for a role. If one is found, returns it, otherwise returns None
        :param used_path - the path in the json that was used to find the name of the entity for which we are trying
        to find a role
        :param payload - the metadata of the series/season/program/scene description
        :param subject_name - the name of the entity we are looking for a role for
        :returns the role name (string), or None if no role is found"""

        # look two steps higher to get all the metadata of the thesaurus item
        concept_metadata = []
        role_field = ""
        if "," not in used_path:
            logger.debug(
                f"Path {used_path} has no higher levels, cannot search for Role"
            )
            return None

        path_parts = used_path.split(",")

        if len(path_parts) < 3:
            logger.debug(f"Path {used_path} is not long enough, cannot search for Role")
            return None

        class_path = ",".join(path_parts[:-2])
        concept_metadata = BaseRdfConcept._get_metadata_value(payload, class_path)

        # the value could be a list, so make sure it always is so can treat everything the same way
        if type(concept_metadata) is not list:
            concept_metadata = [concept_metadata]

        # in flexstore, fields have prefixes. E.g. 'crew.name' and 'crew.role'.  To get the role field, we take
        # the name field and replace 'name' with 'role
        name_metadata_field = path_parts[-2].strip()
        if "name" in name_metadata_field:
            role_field = name_metadata_field.replace("name", "role")

        for concept in concept_metadata:
            if (
                concept[name_metadata_field][path_parts[-1].strip()] == subject_name
            ):  # check we have the right subject
                if role_field in concept:
                    if "resolved_value" in concept[role_field]:
                        return concept[role_field]["resolved_value"]
                    elif "value" in concept[role_field]:
                        return concept[role_field]["value"]

        return None

    def __create_skos_concept(
        self, used_path, payload, concept_label, property_description
    ):
        """Searches in the concept_metadata for a thesaurus concept. If one is found, creates a node for it and
        adds the concept_label as its label, then links it to the parent_node, using the property_uri, and
        sets its type to the range and additionalType values in the property_description
        """
        skos_concept_node = None

        # look one step higher to get all the metadata of the thesaurus item
        concept_metadata = []
        if "," in used_path:
            class_path = ",".join(used_path.split(",")[:-1])
            concept_metadata = BaseRdfConcept._get_metadata_value(payload, class_path)

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

                    # CANNOT DO THIS, because the flex store doesn't provide language attributes
                    # self.graph.add(
                    #     (
                    #         skos_concept_node,
                    #         SKOS.prefLabel,
                    #         Literal(concept_label, lang="nl"),
                    #     )
                    # )
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
                new_payload = BaseRdfConcept._get_metadata_value(payload, path)
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
                                    property_uri,
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
                                (parent_node, property_uri, URIRef(license_url))
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
                            property_uri,
                            Literal(
                                access_text, datatype=property_description["range"]
                            ),
                        )
                    )

                elif (
                    property_description["range"] in self._model.XSD_TYPES
                    and property_uri != self._model.IDENTIFIER
                ):
                    # add the new payload as the value
                    self.graph.add(
                        (
                            parent_node,
                            property_uri,
                            Literal(
                                new_payload_item, datatype=property_description["range"]
                            ),
                        )
                    )
                elif property_uri in SDORdfModel.ASSOCIATED_ROLES_FOR_PROPERTIES:
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

                        # set the rdf type of the property
                        self.graph.add(
                            (
                                concept_node,
                                RDF.type,
                                URIRef(property_description["range"]),
                            )
                        )

                    # create a blank node for the role
                    role_node = BNode()
                    # link the role node to the parent node
                    self.graph.add((parent_node, property_uri, role_node))

                    # try to get more detailed role information
                    role = SDORdfConcept._get_role(used_path, payload, new_payload_item)

                    if role:
                        # for creator (includes crew) or performance roles
                        if property_uri == SDO.byArtist or property_uri == SDO.creator:
                            # try to get uris
                            role_information_list = self.get_matching_role_information(
                                role
                            )

                            if role_information_list:
                                for role_information in role_information_list:
                                    role_uri_node = URIRef(role_information[0])
                                    # add the URI
                                    self.graph.add(
                                        (
                                            role_node,
                                            self._model.ROLE_NAME,
                                            role_uri_node,
                                        )
                                    )
                                    # add its label, if present
                                    if role_information[1]:
                                        self.graph.add(
                                            (
                                                role_uri_node,
                                                RDFS.label,
                                                Literal(role_information[1], lang="nl"),
                                            )
                                        )
                                    # add its type, if present
                                    if role_information[2]:
                                        self.graph.add(
                                            (
                                                role_uri_node,
                                                RDF.type,
                                                URIRef(role_information[2]),
                                            )
                                        )

                            else:
                                # we only have text, add it to the role node as a literal
                                self.graph.add(
                                    (
                                        role_node,
                                        self._model.ROLE_NAME,
                                        Literal(role, lang="nl"),
                                    )
                                )

                        else:
                            # we don't try to find a URI for other role types as we currently
                            # only have mappings for music and production roles.
                            # we just add the text to the role node as a literal
                            self.graph.add(
                                (
                                    role_node,
                                    self._model.ROLE_NAME,
                                    Literal(role, lang="nl"),
                                )
                            )

                    # add the appropriate role type for the property.
                    if (
                        URIRef(property_uri)
                        in SDORdfModel.ASSOCIATED_ROLES_FOR_PROPERTIES
                    ):
                        self.graph.add(
                            (
                                role_node,
                                RDF.type,
                                SDORdfModel.ASSOCIATED_ROLES_FOR_PROPERTIES[
                                    URIRef(property_uri)
                                ],
                            )
                        )

                    # link the concept node to the role node
                    self.graph.add((role_node, property_uri, concept_node))

                elif (
                    "additionalType" in property_description
                    and property_description["additionalType"] == str(SKOS.Concept)
                ) or URIRef(property_uri) == self._model.IDENTIFIER:
                    # In these cases, we have a class as range, but only a simple value in DAAN, as we want
                    # to model a label from DAAN with a skos:Concept in the RDF
                    # create a node for the skos concept

                    # try to create a SKOS concept node
                    concept_node = self.__create_skos_concept(
                        used_path, payload, new_payload_item, property_description
                    )

                    if concept_node is None:
                        if property_uri == self._model.IDENTIFIER:
                            # assume a simple string identifier
                            self.graph.add(
                                (
                                    concept_node,
                                    property_uri,
                                    Literal(new_payload_item, lang="nl"),
                                )
                            )
                        else:
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

                            # set the rdf type of the property
                            self.graph.add(
                                (
                                    concept_node,
                                    RDF.type,
                                    URIRef(property_description["range"]),
                                )
                            )

                            # link to the parent with the property uri
                            self.graph.add(
                                (parent_node, URIRef(property_uri), concept_node)
                            )
                    else:
                        self.graph.add(
                            (parent_node, URIRef(property_uri), concept_node)
                        )
                else:
                    # we have a class as range
                    # create a blank node for the class ID, and a triple to set the type of the class
                    blank_node = BNode()
                    self.graph.add(
                        (blank_node, RDF.type, URIRef(property_description["range"]))
                    )
                    self.graph.add(
                        (parent_node, property_uri, blank_node)
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
