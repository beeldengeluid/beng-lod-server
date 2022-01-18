from rdflib.namespace import XSD

NISV_SCHEMA_NAMESPACE = "http://data.rdlabs.beeldengeluid.nl/schema/"
NISV_DATA_NAMESPACE = "http://data.rdlabs.beeldengeluid.nl/id/"
NISV_SCHEMA_PREFIX = "nisv"
NISV_DATA_PREFIX = "id"

# URIs for concepts in the schema
PROGRAM = NISV_SCHEMA_NAMESPACE + "Program"
SEASON = NISV_SCHEMA_NAMESPACE + "Season"
SERIES = NISV_SCHEMA_NAMESPACE + "Series"
CARRIER = NISV_SCHEMA_NAMESPACE + "Carrier"
CLIP = NISV_SCHEMA_NAMESPACE + "SceneDescription"
ACTING_ENTITY = NISV_SCHEMA_NAMESPACE + "ActingEntity"
HAS_DAAN_PATH = NISV_SCHEMA_NAMESPACE + "hasDaanPath"
IS_CARRIER_OF = NISV_SCHEMA_NAMESPACE + "isCarrierOf"
IS_PART_OF_SERIES = NISV_SCHEMA_NAMESPACE + "isPartOfSeries"
IS_PART_OF_SEASON = NISV_SCHEMA_NAMESPACE + "isPartOfSeason"
IS_PART_OF_PROGRAM = NISV_SCHEMA_NAMESPACE + "isPartOfProgram"

# list of non-gtaa types, so we can use the correct namespace for concepts of this type
NON_GTAA_TYPES = [
    NISV_SCHEMA_NAMESPACE + "TargetGroup",
    NISV_SCHEMA_NAMESPACE + "Broadcaster",
    NISV_SCHEMA_NAMESPACE + "BroadcastStation",
    NISV_SCHEMA_NAMESPACE + "Language",
]

GTAA_NAMESPACE = "http://data.beeldengeluid.nl/gtaa/"
NON_GTAA_NAMESPACE = "http://data.beeldengeluid.nl/nongtaa/"

XSD_TYPES = [
    str(XSD.string),
    str(XSD.int),
    str(XSD.float),
    str(XSD.boolean),
    str(XSD.long),
    str(XSD.dateTime),
    str(XSD.date),
]

# URIs to use for different levels of DAAN records
CLASS_URIS_FOR_DAAN_LEVELS = {
    "SERIES": SERIES,
    "SEASON": SEASON,
    "PROGRAM": PROGRAM,
    "LOGTRACKITEM": CLIP,
    "ITEM": CARRIER,
}
