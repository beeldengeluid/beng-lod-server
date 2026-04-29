from rdflib import Graph

# declare namespaces
SCHEMA = "http://schema.org/"
SDO = "https://schema.org/"
WIKIDATA = "http://www.wikidata.org/entity/"
WIKIDATA_WWW = "http://www.wikidata.org/wiki/"
WIKIDATA_WWW_S = "https://www.wikidata.org/wiki/"
SKOS = "http://www.w3.org/2004/02/skos/core#"
SKOSXL = "http://www.w3.org/2008/05/skos-xl#"
DCTERMS = "http://purl.org/dc/terms/"
DISCOGS = "https://api.discogs.com/artists/"
DISCOGS_ARTIST = "https://www.discogs.com/artist/"
DISCOGS_RELEASE = "https://www.discogs.com/release/"
MUZIEKWEB = "https://data.muziekweb.nl/Link/"
MUZIEKWEB_VOCAB = "https://data.muziekweb.nl/vocab/"
MUZIEKSCHATTEN = "https://data.muziekschatten.nl/som/"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
MUSICBRAINZ_ARTIST = "https://musicbrainz.org/artist/"
MUSICBRAINZ_RELEASE = "https://musicbrainz.org/release/"
QUDT = "http://qudt.org/vocab/unit/"
GTAA = "http://data.beeldengeluid.nl/gtaa/"
BENGTHES = "http://data.beeldengeluid.nl/schema/thes#"
PID = "https://persistent-identifier.nl/"
IED = "https://data.indischherinneringscentrum.nl/ied/"
ALLMUSIC_ARTIST = "https://www.allmusic.com/artist/"
WIKIDATA_PROP_DIRECT_NORMALIZED = "http://www.wikidata.org/prop/direct-normalized/"


def bind_namespaces_to_graph(g: Graph) -> Graph:
    """Binds namespaces to the graph."""
    # add the missing namespaces
    g.bind("skosxl", SKOSXL)
    g.bind("gtaa", GTAA)
    g.bind("sdo", SDO)
    g.bind("bengthes", BENGTHES)
    g.bind("wd", WIKIDATA)
    g.bind("wikidata", WIKIDATA_WWW)
    g.bind("wikidata-s", WIKIDATA_WWW_S)
    g.bind("wikidata-pd", WIKIDATA_PROP_DIRECT_NORMALIZED)
    g.bind("skos", SKOS)
    g.bind("dcterms", DCTERMS)
    g.bind("discogs", DISCOGS)
    g.bind("discogs-artist", DISCOGS_ARTIST)
    g.bind("discogs-release", DISCOGS_RELEASE)
    g.bind("muziekweb", MUZIEKWEB)
    g.bind("som", MUZIEKSCHATTEN)
    g.bind("vocab", MUZIEKWEB_VOCAB)
    g.bind("musicbrainz-artist", MUSICBRAINZ_ARTIST)
    g.bind("musicbrainz-release", MUSICBRAINZ_RELEASE)
    g.bind("qudt", QUDT)
    g.bind("pid", PID)
    g.bind("ied", IED)
    g.bind("schema", SCHEMA)
    g.bind("allmusic-artist", ALLMUSIC_ARTIST)
    return g
