from rdflib import Graph
from models.DAANRdfModel import HAS_DAAN_PATH

"""Imports schema information as a list of classes, their properties, and the paths needed
to retrieve these from the DAAN OAI-PMH"""


class SDOSchemaImporter:
    """ Importer for the RDFS schema definition based on the schema.org.
        TODO: adapt this class to read the schema.org schema.
        NOTE: get the machine readable schema etc. here: https://schema.org/docs/developers.html
    """

    def __init__(self, schemaFile, mappingFile):
        self._graph = Graph()
        self._graph.parse(schemaFile, format="turtle")
        self._graph.parse(mappingFile, format="turtle")

        self._propertiesWithoutDomain = {}
        self._loadPropertiesWithoutDomain()
        assert self._propertiesWithoutDomain, 'ERROR in DAANSchemaImporter: The properties were not loaded.'

        self._classes = {}
        self._loadClasses()

    def getClasses(self):
        return self._classes

    def _loadPropertiesFromQuery(self, query):
        """Returns the properties found by the given query"""

        properties_result = self._graph.query(query)

        properties = {}

        for propertyData in properties_result:
            """ Parses the information about the property from propertyData, and either adds it
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
                    "rangeSuperClass": str(propertyData[3])
                }
                properties[property_uri] = rdf_property

        return properties

    def _loadPropertiesWithoutDomain(self):
        """
            get properties without a domain, these apply (potentially) to all classes
        """
        query = """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{  ?property rdfs:range ?range . \
        ?property <%s> ?path MINUS {?property rdfs:domain ?s}}""" % HAS_DAAN_PATH

        self._propertiesWithoutDomain = self._loadPropertiesFromQuery(query)

    def _loadClasses(self):
        """
        get all classes that have a DAAN path specified (the others are not interesting for LOD)
        """
        query = """SELECT DISTINCT ?class ?path WHERE{?class a rdfs:Class . ?class <%s> ?path}""" % HAS_DAAN_PATH
        classResult = self._graph.query(query)

        # process each class to get its property and path information
        self._classes = {}  # reset the classes member variable
        for row in classResult:
            classUri = str(row[0])
            self._classes[classUri] = self.getClassInfo(classUri)

    def getPropertiesForClass(self, classUri):
        """ get properties belonging to this class (that have this class, or a superclass of this class, as their domain)
        """
        properties = {}

        # first the properties belonging directly to this class
        query = """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{?property rdfs:domain <%s> . 
        ?property rdfs:range ?range . ?property <%s> ?path . OPTIONAL{?range rdfs:subClassOf ?rangeSuperClass}}""" % (
            classUri, HAS_DAAN_PATH)

        properties.update(self._loadPropertiesFromQuery(query))

        # now, the properties belonging to superclasses of this class (which are inherited)
        query = """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{?property rdfs:domain ?s . <%s> rdfs:subClassOf ?s. ?property rdfs:range ?range . ?property <%s> ?path .OPTIONAL{ ?range rdfs:subClassOf ?rangeSuperClass}}""" % (
        classUri, HAS_DAAN_PATH)

        properties.update(self._loadPropertiesFromQuery(query))

        # add in the properties with no domain, as these potentially apply to any class (e.g. hasAdditionalInformation)
        properties.update(self._propertiesWithoutDomain)

        return properties

    def getClassInfo(self, classUri):
        """Gets all the properties belonging to a class, together with the path
            needed to find the values of those properties in DAAN OAI-PMH.
            Returns the information in a dictionary
        """
        classInfo = {}
        classInfo["uri"] = str(classUri)

        # add the properties to the class information
        classInfo['properties'] = self.getPropertiesForClass(classUri)

        return classInfo
