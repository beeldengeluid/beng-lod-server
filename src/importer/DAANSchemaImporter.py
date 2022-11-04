import logging
from rdflib import Graph, URIRef
from models.DAANRdfModel import HAS_DAAN_PATH

"""
Imports schema information as a list of classes, their properties, and the paths needed
to retrieve these from the DAAN OAI-PMH

Importer for the RDFS schema definition based on the DAAN CMS.
"""


class DAANSchemaImporter:
    def __init__(self, schema_file, mapping_file, logger):
        self.logger = logger
        self._graph = Graph()
        self.logger.info(f"Parsing schema file: {schema_file}")
        self._graph.parse(schema_file, format="turtle")
        self.logger.info(f"Parsing mapping file: {mapping_file}")
        self._graph.parse(mapping_file, format="turtle")
        self._propertiesWithoutDomain = {}
        self._load_properties_without_domain()
        self.logger.debug(self._propertiesWithoutDomain)

        # assert self._propertiesWithoutDomain, 'ERROR in DAANSchemaImporter: The properties were not loaded.'
        if not self._propertiesWithoutDomain:
            # things should work when there are nog properties without domain. Thus, just a warning in the log.
            logging.warning("DAANSchemaImporter: The properties without domain were not loaded.")

        self._classes = {}
        self._load_classes()

    def get_classes(self):
        return self._classes

    def _load_properties_from_query(self, query):
        """Returns the properties found by the given query"""

        properties_result = self._graph.query(query)

        properties = {}

        for propertyData in properties_result:
            """Parses the information about the property from propertyData, and either adds it
            to the list of properties, or updates the information for that property.
            """
            property_uri = str(propertyData[0])

            if property_uri in properties:
                # if property has already been described, just add the new path
                properties[property_uri]["paths"].append(str(propertyData[1]))
            else:
                # add the property, complete with its path, range and range superclass
                rdf_property = {
                    "paths": [str(propertyData[1])],
                    "range": str(propertyData[2]),
                    "rangeSuperClass": str(propertyData[3]),
                    "additionalType": str(propertyData[4]),
                }
                properties[property_uri] = rdf_property

        return properties

    def _load_properties_without_domain(self):
        """
        get properties without a domain, these apply (potentially) to all classes
        """
        query = (
            """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass ?additionalType \
        WHERE{  ?property rdfs:range ?range . \
        ?property <%s> ?path MINUS {?property rdfs:domain ?s} . \
        OPTIONAL{?range rdfs:subClassOf ?rangeSuperClass}. \
        OPTIONAL{?range sdo:additionalType ?additionalType}}"""
            % HAS_DAAN_PATH
        )

        self._propertiesWithoutDomain = self._load_properties_from_query(query)

    def _load_classes(self):
        """
        get all classes that have a DAAN path specified (the others are not interesting for LOD)
        """
        query = (
            """SELECT DISTINCT ?class ?path WHERE{?class a rdfs:Class . ?class <%s> ?path}"""
            % HAS_DAAN_PATH
        )
        class_result = self._graph.query(query)

        # process each class to get its property and path information
        self._classes = {}  # reset the classes member variable
        for row in class_result:
            class_uri = str(row[0])
            self._classes[URIRef(class_uri)] = self.get_class_info(class_uri)

    def get_properties_for_class(self, class_uri):
        """get properties belonging to this class (that have this class, or a superclass of this class, as their domain)"""
        properties = {}

        # first the properties belonging directly to this class
        query = """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass ?additionalType \
        WHERE{ ?property rdfs:domain <%s> . \
        ?property rdfs:range ?range . \
        ?property <%s> ?path . \
        OPTIONAL{?range rdfs:subClassOf ?rangeSuperClass}. \
        OPTIONAL{?range sdo:additionalType ?additionalType}}""" % (
            class_uri,
            HAS_DAAN_PATH,
        )

        properties.update(self._load_properties_from_query(query))

        # now, the properties belonging to superclasses of this class (which are inherited)
        query = """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass ?additionalType \
        WHERE{ ?property rdfs:domain ?s . \
        <%s> rdfs:subClassOf* ?s. \
        ?property rdfs:range ?range . \
        ?property <%s> ?path . \
         OPTIONAL{ ?range rdfs:subClassOf ?rangeSuperClass}. \
         OPTIONAL{?range sdo:additionalType ?additionalType}}""" % (
            class_uri,
            HAS_DAAN_PATH,
        )

        properties.update(self._load_properties_from_query(query))

        # add in the properties with no domain, as these potentially apply to any class (e.g. hasAdditionalInformation)
        properties.update(self._propertiesWithoutDomain)

        return properties

    def get_class_info(self, class_uri):
        """Gets all the properties belonging to a class, together with the path
        needed to find the values of those properties in DAAN OAI-PMH.
        Returns the information in a dictionary
        """
        class_info = {
            "uri": str(class_uri),
            # add the properties to the class information
            "properties": self.get_properties_for_class(class_uri),
        }

        return class_info
