import os
from rdflib import Graph, URIRef, Literal, Namespace, XSD
from rdflib.namespace import RDF, SKOS
# from rdflib.plugin import PluginException
# from urllib.parse import urlencode
# from util.APIUtil import APIUtil
from elasticsearch import Elasticsearch, TransportError
import json
from flask import Flask, current_app
from urllib.parse import urlunparse, urlparse
from datetime import datetime


class OpenDataLabHandler:
    """ NISV catalogue data is provided here:
        daan-aggregated-prod-2020 op de server: deves2001

        Problems with daan-aggregated-prod-2020:
        - es data doesn't contain an HTML landing page (the persistent identifier URN:NBN)
        - es data is aggregated (how to resolve something other than a program?
        - es data doesn't contain the GTAA URI's (URI: http://data.beeldengeluid.nl/gtaa/30238), but only the
            label for some field (e.g. "genre": [ "muziekuitvoering" ],
        - es data contains several date formats (can be standardised)

        Description of all data fields and mapping between iMMix and DAAN:
        https://docs.google.com/document/d/1tdI7AEaC5T3LFXABrTdyQOI4pGgqTbIhrECHdu1oXuU/edit#

        TODO: add all the open data fields from here (only inter observer agreement):
        https://docs.google.com/spreadsheets/d/1WnAo1r6UvslCKgpbHaAQZ6lpHL6uiTxcfWLGGI88km0/edit

    """

    def __init__(self, config):
        self.config = config

        self._es = Elasticsearch(
            host=self.config.get('ES_HOST'),
            port=self.config.get('ES_PORT')
        )
        self.index = self.config.get('ES_INDEX')
        self.base_domain = self.config['ODL_BASE_DOMAIN']

    def get_doc_id_from_uri(self, uri=None):
        """ Given a URI, extract the doc_id from it and return that value.
            doc_identifier = "2101608170160873531"  # some example program id
        """
        parts = urlparse(uri)
        path = parts.path
        doc_identifier = path.split('/')[-1]
        return doc_identifier

    def get_uri_from_media_type_and_id(self, doc_id, media_type='media'):
        """ Given the doc_id and the media type, create a valid URI for the resource. """
        scheme = 'http'
        netloc = self.base_domain
        path = '/'.join([media_type, doc_id])
        return urlunparse((scheme, netloc, path, None, None, None))

    def get(self, document_type, doc_id, index=None):
        """ GET: get a typed JSON document from the index based on its id.
        :param document_type: type of document to be fetched
        :param doc_id: identifier for the document to fetch
        :param index: name of the index to get data from
        :return: an elasticsearch document
        :exception: The Elasticsearch transport.perform_request function throws
                a TransportError exception, when the resource is not found. This
                exception must be caught and an HTTP code 404 must be returned.
        """
        if index is None:
            index = self.index
        return self._es.get(index=index, doc_type=document_type, id=doc_id)

    def get_media_item_nisv(self, docu_type="aggregated-program", uri=None, ld_format='xml'):
        """ Returns the RDF for a media item requested for the ODL .
        """
        try:
            headers = {}
            try:
                doc_id = self.get_doc_id_from_uri(uri=uri)
                doc = self.get(document_type=docu_type, doc_id=doc_id)

                # # uncomment to write example json data to file
                # with open('get_aggregated_program_02.json', 'w') as f:
                # 	json_string_from_doc = json.dumps(doc, indent=2)
                # 	f.write(json_string_from_doc)

                rdf_data = self._create_rdf_from_json_dict(json_dict=doc, requested_format=ld_format)
                return rdf_data, 200, headers
            except TransportError as e:
                # in case the requested resource was not found
                print(str(e))
                return {}, 404, headers

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

        # manage namespaces. Basically, we only add our own NISV namespace and schema.org
        ns_sdo = Namespace('http://schema.org/')
        g.namespace_manager.bind('schema', ns_sdo)
        ns_nisv = Namespace('http://data.rdlabs.beeldengeluid.nl/schema/')
        g.namespace_manager.bind('nisv', ns_nisv)

        # extract the item source data
        source = json_dict.get('_source')
        program_id = source.get('program_id')
        program = source.get('program')
        program_site_id = program.get('site_id')
        # program_uri = 'http://data.rdlabs.beeldengeluid.nl/media/%s' % program_id
        program_uri = self.get_uri_from_media_type_and_id(doc_id=program_id)

        # triplify the program
        g.add((URIRef(program_uri), RDF.type, URIRef(ns_nisv.AudioVisualObject)))

        title = program.get('title')[0]
        g.add((URIRef(program_uri), ns_sdo.name, Literal(title, lang='nl')))

        sortdate = program.get('sortdate')[0]
        g.add((URIRef(program_uri), ns_nisv.hasSortDate, Literal(sortdate, datatype=XSD.date)))

        # MATERIAL TYPE, -> no mapping

        # music_genre = program.get('musicgenre')[0]
        # ISSUE: This URI is not part of the source data. This can not be handled with the aggregated index
        # gtaa_id = "http://data.beeldengeluid.nl/gtaa/26074"   # replace the hardcoded URI with a dynamic version
        # g.add((URIRef(program_uri), ns_nisv.hasMusicStyle, URIRef(gtaa_id)))
        # g.add((URIRef(gtaa_id), SKOS.prefLabel, Literal(music_genre, lang='nl')))

        # TODO: SERIES TITLE, THESAURUS TITLE, LICENSOR, EPISODE NUMBER, SUBJECT TERMS, GEOGRAPHICAL NAMES,
        # RECORDING LOCATION, CORPORATIONS, PERSONS, GUEST, CREW, CAST, GENRE, MOTIVATION FOR COMPOSITION,
        # TARGET GROUP, PRODUCTION COMPANY, ASSET RIGHTS (LICENSE), RECORDING INFORMATION,  COLOUR,
        # PUBLICATION, CREATOR, COUNTRY, LANGUAGE, AWARD, IPR TABEL, PRIVACY/ETHICAL TABEL, USED FOOTAGE, PID
        #
        # TODO: series, season, assetItems, logTrackItems, playableContent, [playable, curatedDate, mediaType]

        # format the return document
        data = g.serialize(format=requested_format)

        return data


# It is not allowed to use the flex datastore. Therefore it is commented out.
# class OpenDataLabHandlerFlex:
#     """ NISV catalogue data is provided here:
#
#         Elasticsearch host: dev-es-bng-01.beeldengeluid.nl
#         Head plugin: http://dev-es-bng-01.beeldengeluid.nl/head
#
#         gebruiker: beng
#         password: <you know that>
#         index: starts with 'flexdatastore'
#
#         Several aliases are available and are listed in the config:
#             ES_FLEX_PROGRAM_ALIAS = "flexdatastore-program"
#             ES_FLEX_SERIES_ALIAS = "flexdatastore-series"
#             ES_FLEX_SEASON_ALIAS = "flexdatastore-season"
#             ES_FLEX_ITEM_ALIAS = "flexdatastore-item"
#             ES_FLEX_LOGTRACKITEM_ALIAS = "flexdatastore-logtrackitem"
#
#         Description of all data fields and mapping between iMMix and DAAN:
#         https://docs.google.com/document/d/1tdI7AEaC5T3LFXABrTdyQOI4pGgqTbIhrECHdu1oXuU/edit#
#
#         TODO: add all the open data fields from here (only inter observer agreement):
#         https://docs.google.com/spreadsheets/d/1WnAo1r6UvslCKgpbHaAQZ6lpHL6uiTxcfWLGGI88km0/edit
#     """
#
#     def __init__(self, config):
#         self.config = config
#         self._es = Elasticsearch(
#             host=self.config.get('ES_FLEX_HOST'),
#             port=self.config.get('ES_PORT')
#         )
#         self.base_domain = self.config['ODL_BASE_DOMAIN']
#         self.index = None
#
#     @staticmethod
#     def get_doc_id_from_uri(uri=None):
#         """ Given a URI, extract the doc_id from it and return that value.
#             doc_identifier = "2101608170160873531"  # some example program id
#             doc_identifier = "2101606230008608731"  # example from flexdatastore
#         """
#         parts = urlparse(uri)
#         path = parts.path
#         doc_identifier = path.split('/')[-1]
#         return doc_identifier
#
#     def get_uri_from_media_type_and_id(self, doc_id=None, path='media', media_type=None):
#         """ Given the doc_id and the media type, create a valid URI for the resource.
#         :param: doc_id: the doc_id in the flexdatastore.
#         :param: path: the path after the domain.
#         :param: media_type: the type of media item, e.g. 'program', 'series', 'season', 'scene' (= scenedescription).
#         :returns: a valid URI for the resource
#         """
#         assert doc_id is not None, 'doc_id param is None.'
#         assert media_type is not None, 'No media type was given.'
#
#         scheme = 'http'
#         netloc = self.base_domain
#         path = '/'.join([path, media_type.lower(), doc_id])
#         return urlunparse((scheme, netloc, path, None, None, None))
#
#     def get_uri_for_entry(self, doc_id=None, media_type=None):
#         """
#         :param doc_id:
#         :param media_type:
#         :return: a valid URI for the media item
#         """
#         media_uri = self.base_domain
#         return media_uri
#
#     def get_index_for_media_type(self, resource_type=None):
#         assert resource_type is not None, 'Resource type is not defined'
#         index_types = {
#             'PROGRAM': 'ES_FLEX_PROGRAM_ALIAS',
#             'SERIES': 'ES_FLEX_SERIES_ALIAS',
#             'SEASON': 'ES_FLEX_SEASON_ALIAS',
#             'ITEM': 'ES_FLEX_ITEM_ALIAS',
#             'LOGTRACKITEM': 'ES_FLEX_LOGTRACKITEM_ALIAS'
#         }
#         return index_types.get(resource_type.upper())
#
#     def get(self, document_type, doc_id, index=None):
#         """ GET: get a typed JSON document from the index based on its id.
#         :param document_type: type of document to be fetched
#         :param doc_id: identifier for the document to fetch
#         :param index: name of the index to get data from
#         :return: an elasticsearch document
#         """
#         if index is None:
#             index = self.index
#         return self._es.get(index=index, doc_type=document_type, id=doc_id)
#
#     def get_media_item_nisv(self, docu_type="entry", resource_type=None, uri=None, ld_format='xml'):
#         """ Return the RDF for a specific media item. It can be either a program, series, season or scene description.
#             The identifier for the resource is given as parameter, as is also the document type.
#             The data is retrieved from the flexdatastore.
#
#         :param docu_type: Type of document that is requested.
#         :param resource_type:  Type of the media item that is requested.
#         :param uri: The URI for the resource that is requested
#         :param ld_format: The return format for the requested resource.
#         :return: RDF in the requested return format.
#         """
#         assert resource_type is not None, 'No valid media type was given.'
#
#         self.index = self.get_index_for_media_type(resource_type)
#
#         try:
#             headers = {}
#             try:
#                 doc_id = self.get_doc_id_from_uri(uri=uri)
#                 doc = self.get(document_type=docu_type, doc_id=doc_id)
#
#                 # # uncomment to write example json data to file
#                 # with open('get_flexdatastore_program_%s.json' % doc_id, 'w') as f:
#                 #     json_string_from_doc = json.dumps(doc, indent=2)
#                 #     f.write(json_string_from_doc)
#
#                 rdf_data = self._create_rdf_from_json_dict(json_dict=doc, requested_format=ld_format)
#                 return rdf_data, 200, headers
#             except TransportError as e:
#                 # in case the requested resource was not found
#                 print(str(e))
#                 return {}, 404, headers
#         except Exception as e:
#             print(str(e))
#
#     # def _get_title(self, payload=None, graph=None):
#     #     """
#     #     Example function to create the triples for a title based on the JSON object from the flexdatastore.
#     #     :param payload
#     #     :param: graph: the
#     #     :return: triples for the title of a program
#     #     """
#     #     assert payload is not None, 'The payload for the resource is not given as parameter'
#     #     assert graph is not None, 'The graph object for the resource is not given as parameter'
#     #
#     #     try:
#     #         program_title = payload.get('nisv.title').get('value')
#     #         return URIRef(program_uri), ns_sdo.name, Literal(program_title, lang='nl')
#     #     except ValueError as e:
#     #         print(str(e))
#
#     def _create_rdf_from_json_dict(self, json_dict=None, requested_format='json-ld'):
#         """ This function creates RDF for the NISV metadata coming from the flexdatastore index.
#                 Note: we start with programs first. Other types are discarded
#         :param json_dict: an elasticsearch document containing an NISV item
#         :param requested_format: the expected serialization format
#
#         :return: converted the data to a proper RDF serialization (JSON-LD)
#         """
#         if json_dict is None:
#             return None
#
#         g = Graph()
#
#         # manage namespaces. Basically, we only add our own NISV namespace and schema.org
#         ns_sdo = Namespace('http://schema.org/')
#         g.namespace_manager.bind('schema', ns_sdo)
#         ns_nisv = Namespace('http://data.rdlabs.beeldengeluid.nl/schema/')
#         g.namespace_manager.bind('nisv', ns_nisv)
#
#         # get the item data
#         source = json_dict.get('_source')
#         media_type = json_dict.get('viz_type')
#         site_id = source.get('site_id')
#         program_id = source.get('id')
#         payload = source.get('payload')
#
#         # add class instance for the resource
#         # program_uri = self.get_uri_from_media_type_and_id(doc_id=program_id)
#         program_uri = self.get_uri_from_media_type_and_id(doc_id=program_id, media_type=media_type)
#         g.add((URIRef(program_uri), RDF.type, URIRef(ns_nisv.AudioVisualObject)))
#
#         # TODO: create generic helper funtion
#         # g.add(self._get_title())
#
#         try:
#             program_title = payload.get('nisv.title').get('value')
#             g.add((URIRef(program_uri), ns_sdo.name, Literal(program_title, lang='nl')))
#         except ValueError as e:
#             print(str(e))
#
#         try:
#             series_title = payload.get('nisv.seriestitle').get('value')
#             g.add((URIRef(program_uri), ns_sdo.name, Literal(series_title, lang='nl')))
#         except ValueError as e:
#             print('ValueError with series title')
#
#         try:
#             date_created_ms = source.get('date_created')
#             dt_created = datetime.fromtimestamp(date_created_ms / 1000.0)
#             date_created = dt_created.date()
#             g.add((URIRef(program_uri), ns_nisv.hasCreationDate, Literal(date_created, datatype=XSD.date)))
#         except ValueError as e:
#             print(str(e))
#
#         try:
#             nisv_sourcecatalogue = payload.get('nisv.sourcecatalogue').get('resolved_value')
#             g.add((URIRef(program_uri), ns_nisv.hasSourceCatalog, Literal(nisv_sourcecatalogue, lang='nl')))
#         except ValueError as e:
#             print(str(e))
#
#         try:
#             for parent in source.get('parents'):
#                 if parent.get('parent_type') == 'SERIES':
#                     g.add((URIRef(program_uri),
#                            ns_sdo.partOfSeries,
#                            Literal(parent.get('parent_id'), lang='nl')))
#                 if parent.get('parent_type') == 'SEASON':
#                     g.add((URIRef(program_uri),
#                            ns_sdo.partOfSeason,
#                            Literal(parent.get('parent_id'), lang='nl')))
#         except ValueError as e:
#             print('ValueError with series parent')
#
#         try:
#             for subject in payload.get('nisv.subjectterm'):
#                 notation = subject.get('subjectterm.name').get('value')
#                 pref_label = subject.get('subjectterm.name').get('resolved_value')
#                 gtaa_id = "http://data.beeldengeluid.nl/gtaa/%s" % notation
#                 g.add((URIRef(program_uri), ns_nisv.hasSubject, URIRef(gtaa_id)))
#                 g.add((URIRef(gtaa_id), SKOS.prefLabel, Literal(pref_label, lang='nl')))
#         except ValueError as e:
#             print(str(e))
#
#         # MATERIAL TYPE, -> no mapping
#
#         # music_genre = program.get('musicgenre')[0]
#         # ISSUE: This URI is not part of the source data. This can not be handled with the aggregated index
#         # gtaa_id = "http://data.beeldengeluid.nl/gtaa/26074"   # replace the hardcoded URI with a dynamic version
#         # g.add((URIRef(program_uri), ns_nisv.hasMusicStyle, URIRef(gtaa_id)))
#         # g.add((URIRef(gtaa_id), SKOS.prefLabel, Literal(music_genre, lang='nl')))
#
#         # TODO: SERIES TITLE, THESAURUS TITLE, LICENSOR, EPISODE NUMBER, SUBJECT TERMS, GEOGRAPHICAL NAMES,
#         # RECORDING LOCATION, CORPORATIONS, PERSONS, GUEST, CREW, CAST, GENRE, MOTIVATION FOR COMPOSITION,
#         # TARGET GROUP, PRODUCTION COMPANY, ASSET RIGHTS (LICENSE), RECORDING INFORMATION,  COLOUR,
#         # PUBLICATION, CREATOR, COUNTRY, LANGUAGE, AWARD, IPR TABEL, PRIVACY/ETHICAL TABEL, USED FOOTAGE, PID
#         #
#         # TODO: series, season, assetItems, logTrackItems, playableContent, [playable, curatedDate, mediaType]
#
#         # format the return document
#         data = g.serialize(format=requested_format)
#
#         return data
