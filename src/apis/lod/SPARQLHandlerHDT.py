import logging
from util.APIUtil import APIUtil
from rdflib import Graph
from rdflib_hdt import HDTStore, optimize_sparql
from rdflib_hdt import HDTDocument
from rdflib.plugins.sparql.results.jsonresults import JSONResultParser, JSONResultSerializer
import io
import json


class SPARQLHandlerHDT:
    """ A SPARQL Handler that sends a query to the right place.
    """
    def __init__(self, config):
        self.config = config
        self.hdt_file = self.config.get('HDT_FILE')
        assert self.hdt_file is not None, 'The configuration is missing an HDT file.'
        # self._init_hdt_doc()
        self._init_hdt_graph()

    def _init_hdt_doc(self):
        """ Load an HDT file. Missing indexes are generated automatically, add False as the
        second argument to disable them.
        """
        document = HDTDocument(self.hdt_file)
    
        # Display some metadata about the HDT document itself
        logging.debug(f"Number of RDF triples: {document.total_triples}")
        logging.debug(f"Number of subjects: {document.nb_subjects}")
        logging.debug(f"Number of predicates: {document.nb_predicates}")
        logging.debug(f"Number of objects: {document.nb_objects}")
        logging.debug(f"Number of shared subject-object: {document.nb_shared}")
    
    def _init_hdt_graph(self):
        """ Load an HDT file. Missing indexes are generated automatically.
        You can provide the index file by putting them in the same directory than the HDT file.
        """
        store = HDTStore(self.hdt_file)
        # Display some metadata about the HDT document itself
        logging.debug(f"Number of RDF triples: {len(store)}")
        logging.debug(f"Number of subjects: {store.nb_subjects}")
        logging.debug(f"Number of predicates: {store.nb_predicates}")
        logging.debug(f"Number of objects: {store.nb_objects}")
        logging.debug(f"Number of shared subject-object: {store.nb_shared}")

    def run_query(self, query=None):
        """ Runs a query against an HDT store."""
        # Calling this function optimizes the RDFlib SPARQL engine for HDT documents
        optimize_sparql()
        graph = Graph(store=HDTStore(self.hdt_file))
        results = graph.query(query)
        json_result_serializer = JSONResultSerializer(results)
        data_bytes = io.BytesIO()
        json_result_serializer.serialize(data_bytes, encoding='utf-8')
        # print(data_bytes.getvalue())

        return APIUtil.toSuccessResponse(data_bytes.getvalue())

