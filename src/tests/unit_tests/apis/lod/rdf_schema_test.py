import pytest
import os
import copy
import models.DAANRdfModel as schema
from models.NISVRdfConcept import NISVRdfConcept
from apis.lod.DAANSchemaImporter import DAANSchemaImporter
from util import SettingsUtil

from rdflib import URIRef, Literal
from rdflib.namespace import RDF, XSD
import xmltodict
from flask import Flask
from cache import cache
from urllib.parse import urlparse, urlunparse


def get_uri(cat_type="PROGRAM", daan_id=None):
    if daan_id is None:
        return None
    url_parts = urlparse(schema.NISV_DATA_NAMESPACE)
    path = '/'.join(['resource', cat_type.lower(), daan_id])
    parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
    return urlunparse(parts)


def test_import_schema(application_settings):
    daan_schema = DAANSchemaImporter(application_settings["SCHEMA_FILE"], application_settings["MAPPING_FILE"])
    # print(daan_schema.getClasses())


def test_oai_payload_to_rdf(application_settings, i_program, i_season, i_series, i_carrier, i_clip):
    app = Flask(__name__)
    cache.init_app(app, application_settings)

    # ugly hack - as the storage and OAI versions have different formats, need to select
    # a specific mapping file\
    base_path = SettingsUtil.getBasePath()
    # mappingFile = basePath + os.sep + 'resource' + os.sep + 'daan-mapping.ttl'
    mapping_file = os.path.abspath(os.path.join(base_path, 'resource/daan-mapping.ttl'))
    test_settings = copy.deepcopy(application_settings)
    test_settings["MAPPING_FILE"] = mapping_file

    # classes = DAANSchemaImporter(testSettings["SCHEMA_FILE"], testSettings["MAPPING_FILE"]).getClasses()

    ## PROGRAM
    i_program = i_program.replace("fe:", "")
    program_json = xmltodict.parse(i_program)

    rdf_concept = NISVRdfConcept(program_json["GetRecord"]["record"]["metadata"]["entry"],
                                 "PROGRAM",
                                 test_settings)
    graph = rdf_concept.graph
    graph.serialize(destination='output_program.txt', format='turtle')

    # do some checks
    program_triples = list(graph.triples((rdf_concept.itemNode, None, None)))
    assert len(program_triples) == 27
    assert (rdf_concept.itemNode,
            URIRef(schema.IS_PART_OF_SEASON),
            URIRef(get_uri(cat_type="SEASON", daan_id="2101902260253604731"))
            ) in program_triples

    assert (rdf_concept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasSortDate"),
            Literal("2019-03-26", datatype=XSD.date)
            ) in program_triples

    creators = list(graph.subjects(RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "Creator")))
    assert len(creators) == 1
    for creator in creators:
        personURIs = list(graph.objects(creator, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasPerson")))
        assert len(personURIs) == 1
        creatorName = graph.preferredLabel(personURIs[0])[0][1]
        assert str(creatorName) == "Elsen, Jetske van den"
    publications = list(graph.subjects(RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "PublicationEvent")))
    assert len(publications) == 2
    for publication in publications:
        broadcastStations = list(
            graph.objects(publication, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasBroadcastStation")))
        assert len(broadcastStations) == 0 or len(broadcastStations) == 1
        if broadcastStations:
            stationName = graph.preferredLabel(broadcastStations[0])[0][1]
            assert str(stationName) == "NPO 2"

    graph.serialize(destination='output_program.txt', format='turtle')

    ## SEASON
    i_season = i_season.replace("fe:", "")
    season_json = xmltodict.parse(i_season)
    rdfConcept = NISVRdfConcept(season_json["GetRecord"]["record"]["metadata"]["entry"],
                                "SEASON",
                                test_settings)
    graph = rdfConcept.graph

    # do some checks
    seasonTriples = list(graph.triples((rdfConcept.itemNode, None, None)))
    assert len(seasonTriples) == 20
    assert (rdfConcept.itemNode,
            URIRef(schema.IS_PART_OF_SERIES),
            URIRef(get_uri(cat_type="SERIES", daan_id="2101909080260953431"))
            ) in seasonTriples

    producers = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasProducer")))
    assert len(producers) == 1
    assert (producers[0], URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasRole"),
            Literal("producent", datatype=XSD.string)) in list(graph.triples((producers[0], None, None)))
    productionOrganisations = list(
        graph.objects(producers[0], URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasOrganisation")))
    assert len(productionOrganisations) == 1
    assert (productionOrganisations[0], RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "Organisation")) in list(
        graph.triples((productionOrganisations[0], None, None)))
    productionName = graph.preferredLabel(productionOrganisations[0])[0][1]
    assert str(productionName) == "NTR"
    creators = list(graph.subjects(RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "Creator")))
    assert len(creators) == 12

    graph.serialize(destination='output_season.txt', format='turtle')

    ## SERIES

    i_series = i_series.replace("fe:", "")
    series_json = xmltodict.parse(i_series)
    rdfConcept = NISVRdfConcept(series_json["GetRecord"]["record"]["metadata"]["entry"],
                                "SERIES",
                                test_settings)
    graph = rdfConcept.graph

    # do some checks
    seriesTriples = list(graph.triples((rdfConcept.itemNode, None, None)))
    assert len(seriesTriples) == 9
    mainTitles = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasMainTitle")))
    assert len(mainTitles) == 1
    titleTexts = list(graph.objects(mainTitles[0], URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasTitleText")))
    assert len(titleTexts) == 1
    assert str(titleTexts[0]) == "Dilemma's rond leven en dood"
    subjects = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasSubject")))
    expectedSubjects = ["hindoes", "donors", "euthanasie"]
    for subject in subjects:
        subjectTriples = list(graph.triples((subject, None, None)))
        assert (subject, RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "Subject")) in subjectTriples
        subjectLabel = graph.preferredLabel(subject)[0][1]
        assert str(subjectLabel) in expectedSubjects
    genres = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasGenre")))
    assert len(genres) == 1
    for genre in genres:
        genreTriples = list(graph.triples((genre, None, None)))
        assert (genre, RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "Genre")) in genreTriples
        genreLabel = graph.preferredLabel(genre)[0][1]
        assert str(genreLabel) == "reportage"

    graph.serialize(destination='output_series.txt', format='turtle')

    ## CARRIER

    i_carrier = i_carrier.replace("fe:", "")
    carrier_json = xmltodict.parse(i_carrier)
    rdfConcept = NISVRdfConcept(carrier_json["GetRecord"]["record"]["metadata"]["entry"],
                                "ITEM",
                                test_settings)
    graph = rdfConcept.graph

    # do some checks
    carrierTriples = list(graph.triples((rdfConcept.itemNode, None, None)))
    assert len(carrierTriples) == 7
    creationDates = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasCreationDate")))
    assert len(creationDates) == 1
    assert str(creationDates[0]) == "2008-04-11T21:30:09+00:00"
    programmes = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "isCarrierOf")))
    assert len(programmes) == 2
    for programme in programmes:
        assert str(programme) in [get_uri(cat_type="carrier", daan_id="2101608050034197431"),
                                  get_uri(cat_type="carrier", daan_id="2101608080068352931")]
    carrierTypes = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasCarrierType")))
    assert len(carrierTypes) == 1
    assert str(carrierTypes[0]) == "DAT cassette"

    graph.serialize(destination='output_carrier.txt', format='turtle')

    i_clip = i_clip.replace("fe:", "")
    clip_json = xmltodict.parse(i_clip)
    rdfConcept = NISVRdfConcept(clip_json["GetRecord"]["record"]["metadata"]["entry"], "LOGTRACKITEM", test_settings)
    graph = rdfConcept.graph

    # do some checks
    clipTriples = list(graph.triples((rdfConcept.itemNode, None, None)))
    assert len(clipTriples) == 4
    cat_type = "PROGRAM"
    assert (rdfConcept.itemNode,
            URIRef(schema.IS_PART_OF_PROGRAM),
            URIRef(get_uri(daan_id="2101909160261187331"))
            ) in clipTriples
    mainTitles = list(graph.objects(rdfConcept.itemNode, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasMainTitle")))
    assert len(mainTitles) == 1
    titleTexts = list(graph.objects(mainTitles[0], URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasTitleText")))
    assert len(titleTexts) == 1
    assert str(titleTexts[0]) == "Henk Poort over succes bij Beste Zangers"

    graph.serialize(destination='output_clip.txt', format='turtle')


def test_storage_api_payload_to_rdf(application_settings, i_program_storage, i_season, i_series, i_carrier, i_clip):
    app = Flask(__name__)
    cache.init_app(app, application_settings)

    # ugly hack - as the storage and OAI versions have different formats, need to select
    # a specific mapping file
    base_path = SettingsUtil.getBasePath()
    mapping_file = os.path.abspath(os.path.join(base_path, 'resource/daan-mapping-storage.ttl'))
    test_settings = copy.deepcopy(application_settings)
    test_settings["MAPPING_FILE"] = mapping_file

    ## PROGRAM

    rdfConcept = NISVRdfConcept(i_program_storage, "PROGRAM", test_settings)
    graph = rdfConcept.graph

    graph.serialize(destination='output_program_storage.txt', format='turtle')

    # do some checks
    programTriples = list(graph.triples((rdfConcept.itemNode, None, None)))
    assert len(programTriples) == 27
    assert (rdfConcept.itemNode,
            URIRef(schema.IS_PART_OF_SEASON),
            URIRef(get_uri(cat_type="SEASON", daan_id="2101902260253604731"))
            ) in programTriples

    assert (rdfConcept.itemNode,
            URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasSortDate"),
            Literal("2019-03-26", datatype=XSD.date)
            ) in programTriples
    creators = list(graph.subjects(RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "Creator")))
    assert len(creators) == 1
    for creator in creators:
        personURIs = list(graph.objects(creator, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasPerson")))
        assert len(personURIs) == 1
        creatorName = graph.preferredLabel(personURIs[0])[0][1]
        assert str(creatorName) == "Elsen, Jetske van den"
    publications = list(graph.subjects(RDF.type, URIRef(schema.NISV_SCHEMA_NAMESPACE + "PublicationEvent")))
    assert len(publications) == 2
    for publication in publications:
        broadcastStations = list(
            graph.objects(publication, URIRef(schema.NISV_SCHEMA_NAMESPACE + "hasBroadcastStation")))
        assert len(broadcastStations) == 0 or len(broadcastStations) == 1
        if broadcastStations:
            stationName = graph.preferredLabel(broadcastStations[0])[0][1]
            assert str(stationName) == "NPO 2"
