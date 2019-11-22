from rdflib import Graph

"""Imports schema information as a list of classes, their properties, and the paths needed
to retrieve these from the DAAN OAI-PMH"""

NISV_NAMESPACE = 'http://data.rdlabs.beeldengeluid.nl/schema/'
NISV_PREFIX = "nisv"

# URIs for concepts in the schema
HAS_DAAN_PATH = NISV_NAMESPACE + "hasDaanPath"

class DAANSchemaImporter:
    """
    Importer for the RDFS schema definition based on the DAAN CMS.
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

    def _loadPropertiesWithoutDomain(self):
        """
            get properties without a domain, these apply (potentially) to all classes
        """
        query = """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{  ?property rdfs:range ?range . \
        ?property <%s> ?path MINUS {?property rdfs:domain ?s}}""" % HAS_DAAN_PATH

        propertiesWithoutDomainResult = self._graph.query(query)

        for propertyData in propertiesWithoutDomainResult:
            """ Parses the information about the property from propertyData, and either adds it
                to the list of properties, or updates the information for that property.
            """
            propertyUri = str(propertyData[0])

            if propertyUri in self._propertiesWithoutDomain:
                # if property has already been described, just add the new path
                self._propertiesWithoutDomain[propertyUri]["paths"].append(str(propertyData[1]))
            else:
                # add the property, complete with its path, range and range superclass
                rdfproperty = {
                    "paths": [str(propertyData[1])],
                    "range": str(propertyData[2]),
                    "rangeSuperClass": str(propertyData[3])
                }
                self._propertiesWithoutDomain[propertyUri] = rdfproperty

    def _loadClasses(self):
        """
        get all classes that have a DAAN path specified (the others are not interesting for LOD)
        """
        query = """SELECT DISTINCT ?class ?path WHERE{?class a rdfs:Class . ?class <%s> ?path}"""%HAS_DAAN_PATH
        classResult = self._graph.query(query)

        # process each class to get its property and path information
        self._classes = {}  # reset the classes member variable
        for row in classResult:
            classuri = str(row[0])
            self._classes[classuri] = self.getClassInfo(classuri)

    def getPropertiesForClass(self, classuri):
        """ get properties belonging to this class (that have this class as their domain)
        """
        properties = {}
        query = """SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{?property rdfs:domain <%s> . 
        ?property rdfs:range ?range . ?property <%s> ?path . OPTIONAL{?range rdfs:subClassOf ?rangeSuperClass}}""" % (
            classuri, HAS_DAAN_PATH)

        property_result = self._graph.query(query)

        for propertyData in property_result:
            propertyUri = str(propertyData[0])

            if propertyUri in properties:
                # if property has already been described, just add the new path
                properties[propertyUri]["paths"].append(str(propertyData[1]))
            else:
                # add the property, complete with its path, range and range superclass
                rdfproperty = {
                    "paths": [str(propertyData[1])],
                    "range": str(propertyData[2]),
                    "rangeSuperClass": str(propertyData[3])
                }
                properties[propertyUri] = rdfproperty

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

