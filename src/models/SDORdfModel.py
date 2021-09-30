from rdflib.namespace import XSD

NISV_SCHEMA_NAMESPACE = 'http://data.rdlabs.beeldengeluid.nl/schema/'
SCHEMA_DOT_ORG_NAMESPACE = 'https://schema.org/'
NISV_DATA_NAMESPACE = 'http://data.rdlabs.beeldengeluid.nl/id/'
NISV_SCHEMA_PREFIX = "nisv"
SCHEMA_DOT_ORG_PREFIX = "sdo"
NISV_DATA_PREFIX = "id"

# URIs for concepts in the schema
PROGRAM = SCHEMA_DOT_ORG_NAMESPACE + "CreativeWork"
SEASON = SCHEMA_DOT_ORG_NAMESPACE + "CreativeWorkSeason"
SERIES = SCHEMA_DOT_ORG_NAMESPACE + "CreativeWorkSeries"
CARRIER = SCHEMA_DOT_ORG_NAMESPACE + "MediaObject"
THING = SCHEMA_DOT_ORG_NAMESPACE + "Thing"
PERSON = SCHEMA_DOT_ORG_NAMESPACE + "Person"
ORGANIZATION = SCHEMA_DOT_ORG_NAMESPACE + "Organization"
CLIP = SCHEMA_DOT_ORG_NAMESPACE + "Clip"

# URIS for relations in the schema
HAS_DAAN_PATH = NISV_SCHEMA_NAMESPACE + "hasDaanPath"
IS_CARRIER_OF = SCHEMA_DOT_ORG_NAMESPACE + "associatedMedia"
IS_PART_OF_SERIES = SCHEMA_DOT_ORG_NAMESPACE + "partOfSeries"
IS_PART_OF_SEASON = SCHEMA_DOT_ORG_NAMESPACE + "partOfSeason"
HAS_CLIP = SCHEMA_DOT_ORG_NAMESPACE + "hasPart"
MENTIONS = SCHEMA_DOT_ORG_NAMESPACE + "mentions"
ADDITIONAL_TYPE = SCHEMA_DOT_ORG_NAMESPACE + "additionalType"
CONDITIONS_OF_ACCESS = SCHEMA_DOT_ORG_NAMESPACE + "conditionsOfAccess"
HAS_ASSOCIATED_MEDIA = SCHEMA_DOT_ORG_NAMESPACE + "associatedMedia"
URL = SCHEMA_DOT_ORG_NAMESPACE + "url"
HAS_CONTENT_URL = SCHEMA_DOT_ORG_NAMESPACE + "contentUrl"
IS_MAIN_ENTITY_OF_PAGE = SCHEMA_DOT_ORG_NAMESPACE + "mainEntityOfPage"
#IS_PART_OF_PROGRAM = SCHEMA_DOT_ORG_NAMESPACE + "isPartOfProgram"  # TODO work out how to handle this, is no equivalent property

# TODO: look at how to use the GTAA types
# list of non-gtaa types, so we can use the correct namespace for concepts of this type
NON_GTAA_TYPES = [SCHEMA_DOT_ORG_NAMESPACE + "TargetGroup", NISV_SCHEMA_NAMESPACE + "Broadcaster", NISV_SCHEMA_NAMESPACE + "BroadcastStation",
                  SCHEMA_DOT_ORG_NAMESPACE + "Language"]

GTAA_NAMESPACE = "http://data.beeldengeluid.nl/gtaa/"
NON_GTAA_NAMESPACE = "http://data.beeldengeluid.nl/nongtaa/"

XSD_TYPES = [str(XSD.string), str(XSD.int), str(XSD.float), str(XSD.boolean), str(XSD.long), str(XSD.dateTime),
             str(XSD.date)]

ROLE_TYPES = [PERSON, ORGANIZATION]

# URIs to use for different levels of DAAN records
CLASS_URIS_FOR_DAAN_LEVELS = {"SERIES": SERIES, "SEASON": SEASON, "PROGRAM": PROGRAM, "LOGTRACKITEM": CLIP,
                              "ITEM": CARRIER}

