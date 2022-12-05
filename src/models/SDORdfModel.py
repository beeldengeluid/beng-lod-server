from rdflib.namespace import XSD, SDO

GTAA_NAMESPACE = "http://data.beeldengeluid.nl/gtaa/"
NISV_DATA_NAMESPACE = "http://data.beeldengeluid.nl/id/"
NISV_DATA_PREFIX = "id"
NISV_SCHEMA_NAMESPACE = "http://data.rdlabs.beeldengeluid.nl/schema/"
NISV_SCHEMA_PREFIX = "nisv"
URI_NISV_ORGANISATION = "https://www.beeldengeluid.nl/"

# URIs for concepts in the schema
AUDIO = SDO.AudioObject
CARRIER = SDO.MediaObject
CLIP = SDO.Clip
ORGANIZATION = SDO.Organization
PERSON = SDO.Person
PHOTO = SDO.ImageObject
PROGRAM = SDO.CreativeWork
ROLE_NAME = SDO.roleName
SEASON = SDO.CreativeWorkSeason
SERIES = SDO.CreativeWorkSeries
THING = SDO.Thing
VIDEO = SDO.VideoObject

# URIS for relations in the schema
ADDITIONAL_TYPE = SDO.additionalType
CONDITIONS_OF_ACCESS = SDO.conditionsOfAccess
HAS_ASSOCIATED_MEDIA = SDO.associatedMedia
HAS_CLIP = SDO.hasPart
HAS_CONTENT_URL = SDO.contentUrl
HAS_DAAN_PATH = NISV_SCHEMA_NAMESPACE + "hasDaanPath"
HAS_ENCODING_FORMAT = SDO.encodingFormat
HAS_MATERIAL_TYPE = SDO.material
HAS_PUBLISHER = SDO.publisher
IDENTIFIER = SDO.identifier
IS_CARRIER_OF = SDO.associatedMedia
IS_MAIN_ENTITY_OF_PAGE = SDO.mainEntityOfPage
IS_PART_OF_SEASON = SDO.partOfSeason
IS_PART_OF_SERIES = SDO.partOfSeries
LICENSE = SDO.license
MENTIONS = SDO.mentions
URL = SDO.url
# TODO work out how to handle this, is no equivalent property
# IS_PART_OF_PROGRAM = ??

XSD_TYPES = [
    str(XSD.string),
    str(XSD.int),
    str(XSD.float),
    str(XSD.boolean),
    str(XSD.long),
    str(XSD.dateTime),
    str(XSD.date),
]

ROLE_TYPES = [PERSON, ORGANIZATION]

ASSOCIATED_ROLES_FOR_PROPERTIES = {
    SDO.byArtist: SDO.PerformanceRole,
    SDO.actor: SDO.PerformanceRole,
    SDO.contributor: SDO.PerformanceRole,
    SDO.creator: SDO.PerformanceRole,
    SDO.productionCompany: SDO.Role,
    SDO.mentions: SDO.Role,
}

# URIs to use for different levels of DAAN records
CLASS_URIS_FOR_DAAN_LEVELS = {
    "SERIES": SERIES,
    "SEASON": SEASON,
    "PROGRAM": PROGRAM,
    "LOGTRACKITEM": CLIP,
    "ITEM": CARRIER,
}

# Creative Commons licenses
CC_PDM = "http://creativecommons.org/publicdomain/mark/1.0/"
# CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
CC_BY_SA = "https://creativecommons.org/licenses/by-sa/4.0/"
# CC_BY_NC = 'https://creativecommons.org/licenses/by-nc/4.0/'
# CC_BY_NC_SA = 'https://creativecommons.org/licenses/by-nc-sa/4.0/'
# CC_BY_ND = 'https://creativecommons.org/licenses/by-nd/4.0/'
# CC_BY_NC_ND = 'https://creativecommons.org/licenses/by-nc-nd/4.0/'

# rightsstatements.org licenses
RS_IN_COPYRIGHT = "http://rightsstatements.org/vocab/InC/1.0/"
RS_EU_ORPHAN_WORK = "http://rightsstatements.org/vocab/InC-OW-EU/1.0/"
# RS_EDUCATIONAL_USE_PERMITTED = 'http://rightsstatements.org/vocab/InC-EDU/1.0/'
# RS_CONTRACTUAL_RESTRICTIONS = 'http://rightsstatements.org/vocab/NoC-CR/1.0/'
RS_COPYRIGHT_NOT_EVALUATED = "http://rightsstatements.org/vocab/CNE/1.0/"
RS_OTHER_LEGAL_RESTRICTIONS = "http://rightsstatements.org/vocab/NoC-OKLR/1.0/"

# Tweede Kamer license
TK_AUDIOVISUAL_LICENSE = "https://www.tweedekamer.nl/sites/default/files/atoms/files/licentievoorwaarden_audiovisueel_materiaal_tweede_kamer.pdf"
