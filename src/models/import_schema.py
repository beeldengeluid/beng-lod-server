from rdflib import Graph
from rdflib.namespace import XSD

"""Imports schema information as a list of classes, their properties, and the paths needed
to retrieve these from the DAAN OAI-PMH"""

NISV_NAMESPACE = 'http://data.rdlabs.beeldengeluid.nl/schema/'
NISV_PREFIX = "nisv"

# URIs for concepts in the schema
PROGRAM = NISV_NAMESPACE + "Program"
SEASON = NISV_NAMESPACE + "Season"
SERIES = NISV_NAMESPACE + "Series"
CARRIER = NISV_NAMESPACE + "Carrier"
CLIP = NISV_NAMESPACE + "SceneDescription"
ACTING_ENTITY = NISV_NAMESPACE + "ActingEntity"
HAS_DAAN_PATH = NISV_NAMESPACE + "hasDaanPath"
HAS_CARRIER = NISV_NAMESPACE + "hasCarrier"
IS_PART_OF_SERIES = NISV_NAMESPACE + "isPartOfSeries"
IS_PART_OF_SEASON = NISV_NAMESPACE + "isPartOfSeason"
IS_PART_OF_PROGRAM = NISV_NAMESPACE + "isPartOfProgram"

# list of non-gtaa types, so we can use the correct namespace for concepts of this type
NON_GTAA_TYPES = [NISV_NAMESPACE + "TargetGroup", NISV_NAMESPACE + "Broadcaster", NISV_NAMESPACE + "BroadcastStation", NISV_NAMESPACE + "Language"]

GTAA_NAMESPACE = "http://data.beeldengeluid.nl/gtaa/"
NON_GTAA_NAMESPACE = "http://data.beeldengeluid.nl/nongtaa/"

XSD_TYPES = [str(XSD.string), str(XSD.int), str(XSD.float), str(XSD.boolean), str(XSD.long), str(XSD.dateTime), str(XSD.date)]

# URIs to use for different levels of DAAN records
CLASS_URIS_FOR_DAAN_LEVELS = {"SERIES": SERIES, "SEASON": SEASON, "PROGRAM" : PROGRAM, "LOGTRACKITEM": CLIP, "ITEM": CARRIER}


def importSchema(schemaFile, mappingFile):
    """Imports the classes, properties and the paths to the relevant DAAN variables from the RDF schema
    and returns them as a list of classes, each class containing information on its properties and paths"""

    graph = Graph()
    graph.parse(schemaFile, format="turtle")
    graph.parse(mappingFile, format="turtle")

    # get properties without a domain, these apply (potentially) to all classes
    propertiesWithoutDomain = {}
    propertiesWithoutDomainResult = graph.query("""SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{  ?property rdfs:range ?range . ?property <%s> ?path MINUS {?property rdfs:domain ?s}}"""%HAS_DAAN_PATH)

    for row in propertiesWithoutDomainResult:
        processProperty(row, propertiesWithoutDomain)

    # get all classes that have a DAAN path specified (the others are not interesting for LOD)
    classResult = graph.query("""SELECT DISTINCT ?class ?path WHERE{?class a rdfs:Class . ?class <%s> ?path}"""%HAS_DAAN_PATH)

    # process each class to get its property and path information
    classes = {}
    for row in classResult:
        classes[str(row[0])] = (processClass(str(row[0]), graph, propertiesWithoutDomain))

    return classes


def processProperty(propertyData, properties):
    """Parses the information about the property from propertyData, and either adds it
    to the list of properties, or updates the information for that property"""

    propertyUri = str(propertyData[0])

    if propertyUri in properties:
        # if property has already been described, just add the new path
        properties[propertyUri]["paths"].append(str(propertyData[1]))
    else:
        # add the property, complete with its path, range and range superclass
        property = {}
        property["paths"] = [str(propertyData[1])]
        property["range"] = str(propertyData[2])
        property["rangeSuperClass"] = str(propertyData[3])
        properties[propertyUri] = property

    return


def processClass(classUri, graph, propertiesWithoutDomain):
    """Gets all the properties belonging to a class, together with the path
    needed to find the values of those properties in DAAN OAI-PMH.
    Returns the information in a dictionary"""

    classInfo = {}
    classInfo["uri"] = str(classUri)

    # get properties belonging to this class (that have this class as their domain)
    properties = {}
    propertyResult = graph.query("""SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{?property rdfs:domain <%s> . ?property rdfs:range ?range . ?property <%s> ?path . OPTIONAL{?range rdfs:subClassOf ?rangeSuperClass}}"""%(classUri, HAS_DAAN_PATH))

    for row in propertyResult:
        processProperty(row, properties)

    # get properties that have superclasses of the class as domain (as they are inherited)
    propertyResult = graph.query("""SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{?property rdfs:domain ?s . <%s> rdfs:subClassOf ?s. ?property rdfs:range ?range . ?property <%s> ?path .OPTIONAL{ ?range rdfs:subClassOf ?rangeSuperClass}}"""%(classUri, HAS_DAAN_PATH))

    for row in propertyResult:
        processProperty(row, properties)

    # add in the properties with no domain, as these potentially apply to any class (e.g. hasAdditionalInformation)
    properties.update(propertiesWithoutDomain)

    classInfo['properties'] = properties  # add the properties to the class information

    return classInfo
