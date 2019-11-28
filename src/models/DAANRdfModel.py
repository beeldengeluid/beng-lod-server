from rdflib.namespace import XSD

NISV_NAMESPACE = 'http://data.rdlabs.beeldengeluid.nl/schema/'
NISV_PREFIX = "nisv"

# URIs for concepts in the schema
HAS_DAAN_PATH = NISV_NAMESPACE + "hasDaanPath"

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
NON_GTAA_TYPES = [NISV_NAMESPACE + "TargetGroup", NISV_NAMESPACE + "Broadcaster", NISV_NAMESPACE + "BroadcastStation",
                  NISV_NAMESPACE + "Language"]

GTAA_NAMESPACE = "http://data.beeldengeluid.nl/gtaa/"
NON_GTAA_NAMESPACE = "http://data.beeldengeluid.nl/nongtaa/"

XSD_TYPES = [str(XSD.string), str(XSD.int), str(XSD.float), str(XSD.boolean), str(XSD.long), str(XSD.dateTime),
             str(XSD.date)]

# URIs to use for different levels of DAAN records
CLASS_URIS_FOR_DAAN_LEVELS = {"SERIES": SERIES, "SEASON": SEASON, "PROGRAM": PROGRAM, "LOGTRACKITEM": CLIP,
                              "ITEM": CARRIER}

