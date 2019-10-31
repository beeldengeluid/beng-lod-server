import pytest
import models.import_schema as schema
import models.import_models as model
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, NamespaceManager, SKOS, RDF, XSD
import xmltodict
import json


def test_import_schema(application_settings):
    classes = schema.importSchema(application_settings["SCHEMA_FILE"], application_settings["MAPPING_FILE"])
    print(classes)


def test_payload_to_rdf(application_settings, i_program, i_season, i_series, i_carrier, i_clip):
    nisvNamespace = Namespace(schema.NISV_NAMESPACE)
    namespaceManager = NamespaceManager(Graph())
    namespaceManager.bind(schema.NISV_PREFIX, nisvNamespace)
    namespaceManager.bind("skos", SKOS)

    classes = schema.importSchema(application_settings["SCHEMA_FILE"], application_settings["MAPPING_FILE"])

    ## PROGRAM
    graph = Graph()
    graph.namespace_manager = namespaceManager
    i_program = i_program.replace("fe:", "")
    program_json = xmltodict.parse(i_program)
    programNode = URIRef(program_json["GetRecord"]["record"]["metadata"]["entry"]["id"])
    classUri = schema.PROGRAM
    model.payloadToRdf(program_json["GetRecord"]["record"]["metadata"]["entry"]["payload"], programNode, classUri, classes, graph)
    model.parentToRdf(program_json["GetRecord"]["record"]["metadata"]["entry"], programNode, classUri, graph)

    # do some checks
    programTriples = list(graph.triples((programNode, None, None)))
    assert len(programTriples) == 19
    assert (programNode, URIRef(schema.IS_PART_OF_SEASON), URIRef(schema.NISV_NAMESPACE + "2101902260253604731")) in programTriples
    assert (programNode, URIRef(schema.NISV_NAMESPACE + "hasSortDate"), Literal("2019-03-26", datatype=XSD.date)) in programTriples
    creators = list(graph.subjects(RDF.type, URIRef(schema.NISV_NAMESPACE + "Creator")))
    assert len(creators) == 1
    for creator in creators:
        personURIs = list(graph.objects(creator, URIRef(schema.NISV_NAMESPACE + "hasPerson")))
        assert len(personURIs) == 1
        creatorName = graph.preferredLabel(personURIs[0])[0][1]
        assert str(creatorName) == "Elsen, Jetske van den"
    publications = list(graph.subjects(RDF.type, URIRef(schema.NISV_NAMESPACE + "PublicationEvent")))
    assert len(publications) == 2
    for publication in publications:
        broadcastStations = list(graph.objects(publication, URIRef(schema.NISV_NAMESPACE + "hasBroadcastStation")))
        assert len(broadcastStations) == 0 or len(broadcastStations)==1
        if broadcastStations:
            stationName = graph.preferredLabel(broadcastStations[0])[0][1]
            assert str(stationName) == "NPO 2"

    graph.serialize(destination='output_program.txt', format='turtle')

    ## SEASON
    graph = Graph()
    graph.namespace_manager = namespaceManager
    i_season = i_season.replace("fe:", "")
    season_json = xmltodict.parse(i_season)
    seasonNode = URIRef(season_json["GetRecord"]["record"]["metadata"]["entry"]["id"])
    classUri = schema.SEASON
    model.payloadToRdf(season_json["GetRecord"]["record"]["metadata"]["entry"]["payload"], seasonNode, classUri, classes, graph)
    model.parentToRdf(season_json["GetRecord"]["record"]["metadata"]["entry"], seasonNode, classUri, graph)

    # do some checks
    seasonTriples = list(graph.triples((seasonNode, None, None)))
    assert len(seasonTriples) == 19
    assert (seasonNode, URIRef(schema.IS_PART_OF_SERIES), URIRef(schema.NISV_NAMESPACE + "2101909080260953431")) in seasonTriples
    producers = list(graph.objects(seasonNode, URIRef(schema.NISV_NAMESPACE + "hasProducer")))
    assert len(producers) == 1
    assert (producers[0], URIRef(schema.NISV_NAMESPACE + "hasRole"), Literal("producent", datatype=XSD.string)) in list(graph.triples((producers[0], None, None)))
    productionOrganisations = list(graph.objects(producers[0], URIRef(schema.NISV_NAMESPACE + "hasOrganisation")))
    assert len(productionOrganisations) == 1
    assert (productionOrganisations[0], RDF.type, URIRef(schema.NISV_NAMESPACE + "Organisation")) in list(graph.triples((productionOrganisations[0], None, None)))
    productionName = graph.preferredLabel(productionOrganisations[0])[0][1]
    assert str(productionName) == "NTR"
    creators = list(graph.subjects(RDF.type, URIRef(schema.NISV_NAMESPACE + "Creator")))
    assert len(creators) == 12

    graph.serialize(destination='output_season.txt', format='turtle')

    ## SERIES

    graph = Graph()
    graph.namespace_manager = namespaceManager
    i_series = i_series.replace("fe:", "")
    series_json = xmltodict.parse(i_series)
    seriesNode = URIRef(series_json["GetRecord"]["record"]["metadata"]["entry"]["id"])
    classUri = schema.SERIES
    model.payloadToRdf(series_json["GetRecord"]["record"]["metadata"]["entry"]["payload"], seriesNode, classUri, classes, graph)
    model.parentToRdf(series_json["GetRecord"]["record"]["metadata"]["entry"], seriesNode, classUri, graph)

    # do some checks
    seriesTriples = list(graph.triples((seriesNode, None, None)))
    assert len(seriesTriples) == 8
    mainTitles = list(graph.objects(seriesNode, URIRef(schema.NISV_NAMESPACE + "hasMainTitle")))
    assert len(mainTitles) == 1
    titleTexts = list(graph.objects(mainTitles[0], URIRef(schema.NISV_NAMESPACE + "hasTitleText")))
    assert len(titleTexts) == 1
    assert str(titleTexts[0]) == "Dilemma's rond leven en dood"
    subjects = list(graph.objects(seriesNode, URIRef(schema.NISV_NAMESPACE + "hasSubject")))
    expectedSubjects = ["hindoes", "donors", "euthanasie"]
    for subject in subjects:
        subjectTriples = list(graph.triples((subject, None, None)))
        assert (subject, RDF.type, URIRef(schema.NISV_NAMESPACE + "Subject")) in subjectTriples
        subjectLabel = graph.preferredLabel(subject)[0][1]
        assert str(subjectLabel) in expectedSubjects
    genres = list(graph.objects(seriesNode, URIRef(schema.NISV_NAMESPACE + "hasGenre")))
    assert len(genres) == 1
    for genre in genres:
        genreTriples = list(graph.triples((genre, None, None)))
        assert (genre, RDF.type, URIRef(schema.NISV_NAMESPACE + "Genre")) in genreTriples
        genreLabel = graph.preferredLabel(genre)[0][1]
        assert str(genreLabel) == "reportage"

    graph.serialize(destination='output_series.txt', format='turtle')

    ## CARRIER

    graph = Graph()
    graph.namespace_manager = namespaceManager
    i_carrier = i_carrier.replace("fe:", "")
    carrier_json = xmltodict.parse(i_carrier)
    carrierNode = URIRef(carrier_json["GetRecord"]["record"]["metadata"]["entry"]["id"])
    classUri = schema.CARRIER
    model.payloadToRdf(carrier_json["GetRecord"]["record"]["metadata"]["entry"]["payload"], carrierNode, classUri, classes, graph)
    model.parentToRdf(carrier_json["GetRecord"]["record"]["metadata"]["entry"], carrierNode, classUri, graph)

    # do some checks
    carrierTriples = list(graph.triples((carrierNode, None, None)))
    assert len(carrierTriples) == 4
    creationDates = list(graph.objects(carrierNode, URIRef(schema.NISV_NAMESPACE + "hasCreationDate")))
    assert len(creationDates) == 1
    assert str(creationDates[0]) == "2008-04-11T21:30:09+00:00"
    programmes = list(graph.subjects(URIRef(schema.NISV_NAMESPACE + "hasCarrier"), carrierNode))
    assert len(programmes) == 2
    for programme in programmes:
        assert str(programme) == schema.NISV_NAMESPACE + "2101608050034197431" or str(programme) == schema.NISV_NAMESPACE + "2101608080068352931"
    carrierTypes = list(graph.objects(carrierNode, URIRef(schema.NISV_NAMESPACE + "hasCarrierType")))
    assert len(carrierTypes) == 1
    assert str(carrierTypes[0]) == "DAT cassette"

    graph.serialize(destination='output_carrier.txt', format='turtle')

    graph = Graph()
    graph.namespace_manager = namespaceManager
    i_clip = i_clip.replace("fe:", "")
    clip_json = xmltodict.parse(i_clip)
    clipNode = URIRef(clip_json["GetRecord"]["record"]["metadata"]["entry"]["id"])
    classUri = schema.CLIP
    model.payloadToRdf(clip_json["GetRecord"]["record"]["metadata"]["entry"]["payload"], clipNode, classUri, classes, graph)
    model.parentToRdf(clip_json["GetRecord"]["record"]["metadata"]["entry"], clipNode, classUri, graph)

    # do some checks
    clipTriples = list(graph.triples((clipNode, None, None)))
    assert len(clipTriples) == 3
    assert (clipNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + "2101909160261187331")) in clipTriples
    mainTitles = list(graph.objects(clipNode, URIRef(schema.NISV_NAMESPACE + "hasMainTitle")))
    assert len(mainTitles) == 1
    titleTexts = list(graph.objects(mainTitles[0], URIRef(schema.NISV_NAMESPACE + "hasTitleText")))
    assert len(titleTexts) == 1
    assert str(titleTexts[0]) == "Henk Poort over succes bij Beste Zangers"

    graph.serialize(destination='output_clip.txt', format='turtle')

