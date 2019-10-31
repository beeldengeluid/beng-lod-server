from rdflib import Graph
from rdflib.namespace import XSD

NISV_NAMESPACE = 'http://data.rdlabs.beeldengeluid.nl/schema/'
NISV_PREFIX = "nisv"

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

NON_GTAA_TYPES = [NISV_NAMESPACE + "TargetGroup", NISV_NAMESPACE + "Broadcaster", NISV_NAMESPACE + "BroadcastStation", NISV_NAMESPACE + "Language"]

GTAA_NAMESPACE = "http://data.beeldengeluid.nl/gtaa/"
NON_GTAA_NAMESPACE = "http://data.beeldengeluid.nl/nongtaa/"

XSD_TYPES = [str(XSD.string), str(XSD.int), str(XSD.float), str(XSD.boolean), str(XSD.long), str(XSD.dateTime), str(XSD.date)]

CLASS_URIS_FOR_DAAN_LEVELS = {"SERIES": SERIES, "SEASON": SEASON, "PROGRAM" : PROGRAM, "LOGTRACKITEM": CLIP, "ITEM": CARRIER}

def importSchema(schemaFile, mappingFile):
    '''Imports the classes, properties and the paths to the relevant DAAN variables from the RDF schema'''

    graph = Graph()
    graph.parse(schemaFile, format="turtle")
    graph.parse(mappingFile, format="turtle")

    # get properties without a domain, these apply (potentially) to all classes
    propertiesWithoutDomain = {}
    propertiesWithoutDomainResult = graph.query("""SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{  ?property rdfs:range ?range . ?property <%s> ?path MINUS {?property rdfs:domain ?s}}"""%HAS_DAAN_PATH)

    for row in propertiesWithoutDomainResult:
        processProperty(row, propertiesWithoutDomain)

    classResult = graph.query("""SELECT DISTINCT ?class ?path WHERE{?class a rdfs:Class . ?class <%s> ?path}"""%HAS_DAAN_PATH)

    classes = {}
    for row in classResult:
        classes[str(row[0])] = (processClass(str(row[0]), graph, propertiesWithoutDomain))

    return classes

def processProperty(row, properties):
    propertyUri = str(row[0])

    if propertyUri in properties:
        # just add an extra path
        properties[propertyUri]["paths"].append(str(row[1]))
    else:
        # add the property
        property = {}
        property["paths"] = [str(row[1])]
        property["range"] = str(row[2])
        property["rangeSuperClass"] = str(row[3])
        properties[propertyUri] = property

    return

def processClass(classUri, graph, propertiesWithoutDomain):
    classInfo = {}
    classInfo["uri"] = str(classUri)

    # get properties that have class as domain
    properties = {}
    propertyResult = graph.query("""SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{?property rdfs:domain <%s> . ?property rdfs:range ?range . ?property <%s> ?path . OPTIONAL{?range rdfs:subClassOf ?rangeSuperClass}}"""%(classUri, HAS_DAAN_PATH))

    for row in propertyResult:
        processProperty(row, properties)

    # get properties that have superclasses of the class as domain
    propertyResult = graph.query("""SELECT DISTINCT ?property ?path ?range ?rangeSuperClass WHERE{?property rdfs:domain ?s . <%s> rdfs:subClassOf ?s. ?property rdfs:range ?range . ?property <%s> ?path .OPTIONAL{ ?range rdfs:subClassOf ?rangeSuperClass}}"""%(classUri, HAS_DAAN_PATH))

    for row in propertyResult:
        processProperty(row, properties)

    # add in the properties with no domain
    properties.update(propertiesWithoutDomain)

    classInfo['properties'] = properties
    return classInfo
