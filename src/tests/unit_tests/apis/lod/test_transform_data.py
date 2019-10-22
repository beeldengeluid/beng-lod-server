from apis.lod.LODHandler import LODHandler
from flask import current_app
from lxml import etree
from rdflib import Graph


def test_transform_program(get_record_xml_local_uri):
    handler = LODHandler({"XSLT_FILE":"test.xsl"})
    doctree = handler.getElementTreeFromXMLDoc(get_record_xml_local_uri)
    result = handler.transformFromDocTree(doctree)
    # graph = Graph()
    # xmldata = etree.tostring(result, encoding='UTF-8')
    # graph.parse(data=xmldata)
    # xmlns = result.getroot().nsmap
    # graph.serialize("test_output.rdf", context=xmlns, format="turtle")

