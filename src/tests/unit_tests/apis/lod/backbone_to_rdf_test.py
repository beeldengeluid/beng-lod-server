from api.BackboneHandler import BackboneHandler
import models.import_schema as schema
from util.TurtleStorageHandler import TurtleStorageHandler
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from mockito import when, unstub
import os

"""This tests the whole pipeline from backbone handler to storing RDF in a turtle file. So technically
it's a little more of an integration test, but all the code is in this project"""

"""--------------------------- POST ---------------------------"""
def test_post_program(application_settings, i_program):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        programNode = URIRef(schema.NISV_NAMESPACE + "2101708210027914131")
        testStatements = []
        testStatements.append((programNode, RDF.type, URIRef(schema.PROGRAM)))
        testStatements.append((programNode, URIRef(schema.IS_PART_OF_SEASON), URIRef(schema.NISV_NAMESPACE + "2101708180022214931")))
        create_and_test_rdf(application_settings, testStorageLocation, i_program, programNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_post_series(application_settings, i_series):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        seriesNode = URIRef(schema.NISV_NAMESPACE + "2101704030017904231")
        testStatements = []
        testStatements.append((seriesNode, RDF.type, URIRef(schema.SERIES)))
        create_and_test_rdf(application_settings, testStorageLocation, i_series, seriesNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_post_season(application_settings, i_season):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        seasonNode = URIRef(schema.NISV_NAMESPACE + "2101708180022214931")
        testStatements = []
        testStatements.append((seasonNode, RDF.type, URIRef(schema.SEASON)))
        testStatements.append((seasonNode, URIRef(schema.IS_PART_OF_SERIES), URIRef(schema.NISV_NAMESPACE + "2101704030017904231")))
        create_and_test_rdf(application_settings, testStorageLocation, i_season, seasonNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_post_clip(application_settings, i_clip):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        clipNode = URIRef(schema.NISV_NAMESPACE + "2101901300081049624")
        testStatements = []
        testStatements.append((clipNode, RDF.type, URIRef(schema.CLIP)))
        testStatements.append((clipNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + "2101708200026397731")))
        create_and_test_rdf(application_settings, testStorageLocation, i_clip, clipNode, testStatements)
    finally:
        unstub()
        cleanup(testStorageLocation)

"""--------------------------- PUT ---------------------------"""
def test_put_program(application_settings, i_program):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        programNode = URIRef(schema.NISV_NAMESPACE + "2101708210027914131")
        testStatements = []
        testStatements.append((programNode, RDF.type, URIRef(schema.PROGRAM)))
        testStatements.append((programNode, URIRef(schema.IS_PART_OF_SEASON), URIRef(schema.NISV_NAMESPACE + "2101708180022214931")))
        update_and_test_rdf(application_settings, testStorageLocation, i_program, programNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_put_series(application_settings, i_series):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        seriesNode = URIRef(schema.NISV_NAMESPACE + "2101704030017904231")
        testStatements = []
        testStatements.append((seriesNode, RDF.type, URIRef(schema.SERIES)))
        update_and_test_rdf(application_settings, testStorageLocation, i_series, seriesNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_put_season(application_settings, i_season):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        seasonNode = URIRef(schema.NISV_NAMESPACE + "2101708180022214931")
        testStatements = []
        testStatements.append((seasonNode, RDF.type, URIRef(schema.SEASON)))
        testStatements.append((seasonNode, URIRef(schema.IS_PART_OF_SERIES), URIRef(schema.NISV_NAMESPACE + "2101704030017904231")))
        update_and_test_rdf(application_settings, testStorageLocation, i_season, seasonNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_put_clip(application_settings, i_clip):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        clipNode = URIRef(schema.NISV_NAMESPACE + "2101901300081049624")
        testStatements = []
        testStatements.append((clipNode, RDF.type, URIRef(schema.CLIP)))
        testStatements.append((clipNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + "2101708200026397731")))
        update_and_test_rdf(application_settings, testStorageLocation, i_clip, clipNode, testStatements)
    finally:
        unstub()
        cleanup(testStorageLocation)

"""--------------------------- DELETE ---------------------------"""
def test_delete_program(application_settings, i_program):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        programNode = URIRef(schema.NISV_NAMESPACE + "2101708210027914131")
        testStatements = []
        testStatements.append((programNode, RDF.type, URIRef(schema.PROGRAM)))
        testStatements.append((programNode, URIRef(schema.IS_PART_OF_SEASON), URIRef(schema.NISV_NAMESPACE + "2101708180022214931")))
        delete_and_test_rdf(application_settings, testStorageLocation, i_program, programNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_delete_series(application_settings, i_series):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        seriesNode = URIRef(schema.NISV_NAMESPACE + "2101704030017904231")
        testStatements = []
        testStatements.append((seriesNode, RDF.type, URIRef(schema.SERIES)))
        delete_and_test_rdf(application_settings, testStorageLocation, i_series, seriesNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_delete_season(application_settings, i_season):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        seasonNode = URIRef(schema.NISV_NAMESPACE + "2101708180022214931")
        testStatements = []
        testStatements.append((seasonNode, RDF.type, URIRef(schema.SEASON)))
        testStatements.append((seasonNode, URIRef(schema.IS_PART_OF_SERIES), URIRef(schema.NISV_NAMESPACE + "2101704030017904231")))
        delete_and_test_rdf(application_settings, testStorageLocation, i_season, seasonNode, testStatements)

    finally:
        unstub()
        cleanup(testStorageLocation)

def test_delete_clip(application_settings, i_clip):
    testStorageLocation = os.getcwd() + os.sep + "test_storage" + os.sep
    try:
        clipNode = URIRef(schema.NISV_NAMESPACE + "2101901300081049624")
        testStatements = []
        testStatements.append((clipNode, RDF.type, URIRef(schema.CLIP)))
        testStatements.append((clipNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + "2101708200026397731")))
        delete_and_test_rdf(application_settings, testStorageLocation, i_clip, clipNode, testStatements)
    finally:
        unstub()
        cleanup(testStorageLocation)


def create_and_test_rdf(application_settings, testStorageLocation, testInput, node, testStatements):
    if not os.path.exists(testStorageLocation):
        os.mkdir(testStorageLocation)
    when(TurtleStorageHandler).createStorage().thenReturn(testStorageLocation)
    bh = BackboneHandler(application_settings)
    bh.processNewData(testInput)

    assert os.path.exists(testStorageLocation + bh.storageHandler.tripleFile)

    g = Graph()
    g.parse(testStorageLocation + bh.storageHandler.tripleFile, format="ttl")

    for testStatement in testStatements:
        assert testStatement in g.triples((node, None, None))

def update_and_test_rdf(application_settings, testStorageLocation, testInput, node, testStatements):
    if not os.path.exists(testStorageLocation):
        os.mkdir(testStorageLocation)
    when(TurtleStorageHandler).createStorage().thenReturn(testStorageLocation)
    bh = BackboneHandler(application_settings)
    bh.processUpdatedData(testInput)

    assert os.path.exists(testStorageLocation + bh.storageHandler.tripleFile)

    g = Graph()
    g.parse(testStorageLocation + bh.storageHandler.tripleFile, format="ttl")

    for testStatement in testStatements:
        assert testStatement in g.triples((node, None, None))

    assert os.path.exists(bh.storageHandler.storageLocation + bh.storageHandler.updatesFile)

    with open(bh.storageHandler.storageLocation + bh.storageHandler.updatesFile) as f:
        updateIds = f.read().splitlines()

    assert testInput["id"] in updateIds


def delete_and_test_rdf(application_settings, testStorageLocation, testInput, node, testStatements):
    if not os.path.exists(testStorageLocation):
        os.mkdir(testStorageLocation)
    when(TurtleStorageHandler).createStorage().thenReturn(testStorageLocation)
    bh = BackboneHandler(application_settings)
    bh.processDeletedData(testInput)

    assert os.path.exists(bh.storageHandler.storageLocation + bh.storageHandler.deletionsFile)

    with open(bh.storageHandler.storageLocation + bh.storageHandler.deletionsFile) as f:
        deleteIds = f.read().splitlines()

    assert testInput["id"] in deleteIds

def cleanup(storageLocation):
    for the_file in os.listdir(storageLocation):
        file_path = os.path.join(storageLocation, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except:
            raise SystemError("Failed to remove files")
    os.rmdir(storageLocation)