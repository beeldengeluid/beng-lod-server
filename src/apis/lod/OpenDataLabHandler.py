import os
from rdflib import Graph, URIRef, Literal, Namespace, XSD
from rdflib.namespace import RDF, SKOS
# from rdflib.plugin import PluginException
# from urllib.parse import urlencode
# from util.APIUtil import APIUtil
from elasticsearch import Elasticsearch
import json
from flask import Flask, current_app

# from urllib.urlparse import urlunparse


class OpenDataLabHandler(object):
    """ NISV catalogue data is provided here:
        daan-aggregated-prod-2020 op de server: deves2001

        Alternatief onderzoeken: niet geaggregeerde index:
        http://dev-es-bng-01.beeldengeluid.nl/head
        gebruiker: beng
        password: <you know that>
        index: starts with 'flexdatastore'

        Onderzoeksvraag:
            Welke index biedt de beste mogelijkheden om media resources op te vragen?

        Problems with daan-aggregated-prod-2020:
        - es data doesn't contain an HTML landing page (the persistent identifier URN:NBN)
        - es data is aggregated (how to resolve something other than a program?
        - es data doesn't contain the GTAA URI's (URI: http://data.beeldengeluid.nl/gtaa/30238), but only the
            label for some field (e.g. "genre": [ "muziekuitvoering" ],
        - es data contains several date formats (can be standardised)

        TODO: add all the open data fields from here (only inter observer agreement):
        https://docs.google.com/spreadsheets/d/1WnAo1r6UvslCKgpbHaAQZ6lpHL6uiTxcfWLGGI88km0/edit
    """

    def __init__(self, config):
        self.config = config

        self._es = Elasticsearch(
            host=self.config.get('ES_HOST'),
            port=self.config.get('ES_PORT')
        )

        # make sure the path can be read (use app context)
        # see https://flask.palletsprojects.com/en/1.1.x/appcontext/
        app = Flask(__name__)
        with app.app_context():
            app_path = os.path.dirname(os.path.realpath(current_app.instance_path))
            self.base_domain = os.path.join(app_path, self.config['ODL_BASE_DOMAIN'])

        self.index = self.config.get('ES_INDEX')

    def get_doc_id_from_uri(self, uri=None):
        """ Given a URI, extract the doc_id from it and return that value. """
        if uri is None:
            doc_identifier = "2101608170160873531"  # some example program id
        else:
            doc_identifier = uri

        return doc_identifier

    def get_uri_from_media_type_and_id(self, media_type, doc_id):
        """ Given the doc_id and the media type, create a valid URI for the resource. """
        protocol = 'http'
        base_domain = self.base_domain

        # urlunparse(protocol, )
        return None

    def get(self, document_type, doc_id, index=None):
        """ GET: get a typed JSON document from the index based on its id.
        :param document_type: type of document to be fetched
        :param doc_id: identifier for the document to fetch
        :param index: name of the index to get data from
        :return: an elasticsearch document
        """
        if not index:
            index = self.index

        return self._es.get(index=index, doc_type=document_type, id=doc_id)

    def get_media_item_nisv(self, docu_type="aggregated-program", uri=None, ld_format='xml'):
        """ Returns the RDF for a media item requested for the ODL .
        """
        try:
            if docu_type is None:
                docu_type = "aggregated-program"
            doc_id = self.get_doc_id_from_uri(uri=uri)
            doc = self.get(document_type=docu_type, doc_id=doc_id)

            # # uncomment to write example json data to file
            # with open('get_aggregated_program_02.json', 'w') as f:
            # 	json_string_from_doc = json.dumps(doc, indent=2)
            # 	f.write(json_string_from_doc)

            rdf_data = self._create_rdf_from_json_dict(json_dict=doc, requested_format=ld_format)

            headers = {}
            return rdf_data, 200, headers
        except Exception as e:
            print(str(e))

    def _create_rdf_from_json_dict(self, json_dict=None, requested_format='json-ld'):
        """ This function creates RDF for the NISV metadata coming from the Elasticsearch aggregated index.

        :param json_dict: an elasticsearch document containing an aggregated item
        :param requested_format: the expected serialization format

        :return: converted the data to a proper RDF serialization (JSON-LD)
        """
        if json_dict is None:
            return None

        g = Graph()
        SDO = Namespace('http://schema.org/')
        g.namespace_manager.bind('schema', SDO)
        NISV = Namespace('http://data.rdlabs.beeldengeluid.nl/schema/')
        g.namespace_manager.bind('nisv', NISV)

        source = json_dict.get('_source')
        program_id = source.get('program_id')
        program = source.get('program')
        program_site_id = program.get('site_id')
        program_uri = 'http://data.rdlabs.beeldengeluid.nl/media/%s' % program_id

        # TODO: triplify the program
        g.add((URIRef(program_uri), RDF.type, URIRef(NISV.AudioVisualObject)))

        title = program.get('title')[0]
        g.add((URIRef(program_uri), SDO.name, Literal(title, lang='nl')))

        sortdate = program.get('sortdate')[0]
        g.add((URIRef(program_uri), NISV.hasSortDate, Literal(sortdate, datatype=XSD.date)))

        # MATERIAL TYPE, -> no mapping

        music_genre = program.get('musicgenre')[0]

        # TODO: remove the hardcoded URI
        gtaa_id = "http://data.beeldengeluid.nl/gtaa/26074"
        g.add((URIRef(program_uri), NISV.hasMusicStyle, URIRef(gtaa_id)))
        g.add((URIRef(gtaa_id), SKOS.prefLabel, Literal(music_genre, lang='nl')))

        # TODO: SERIES TITLE, THESAURUS TITLE, LICENSOR, EPISODE NUMBER, SUBJECT TERMS, GEOGRAPHICAL NAMES,
        # RECORDING LOCATION, CORPORATIONS, PERSONS, GUEST, CREW, CAST, GENRE, MOTIVATION FOR COMPOSITION,
        # TARGET GROUP, PRODUCTION COMPANY, ASSET RIGHTS (LICENSE), RECORDING INFORMATION,  COLOUR,
        # PUBLICATION, CREATOR, COUNTRY, LANGUAGE, AWARD, IPR TABEL, PRIVACY/ETHICAL TABEL, USED FOOTAGE, PID
        #
        # TODO: series, season, assetItems, logTrackItems, playableContent, [playable, curatedDate, mediaType]

        # format the return document
        data = g.serialize(format=requested_format)

        return data
#
# def _serialize_rdf(self, rdf_data=None, requested_format='xml'):
# 	""" Return an RDF serialization conform the requested_format parameter
#
# 	:param rdf_data:
# 	:param requested_format: the user provided Acceptable return type
# 	:return: the rdf data in the requested serialization
# 	"""
# 	if rdf_data is None:
# 		return None
# 	g = Graph()
# 	g.parse(rdf_data)
# 	data = g.serialize(format=requested_format)
# 	return data
