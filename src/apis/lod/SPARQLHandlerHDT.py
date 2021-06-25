from rdflib import Graph
# from rdflib_hdt import HDTStore
# from rdflib.namespace import FOAF
# from rdflib_hdt import HDTDocument


class SPARQLHandlerHDT:
    """ A SPARQL Handler that sends a query to the right place.
    """
    def __init__(self, config):
        self.config = config
        self.hdt_file = self.config.get('HDT_FILE')
        assert self.hdt_file is not None, 'The configuration is missing an HDT file.'

    def _init_hdt_doc(self):
        """ Load an HDT file. Missing indexes are generated automatically, add False as the
        second argument to disable them.
        """
        pass
        # document = HDTDocument(self.hdt_file)
        #
        # # Display some metadata about the HDT document itself
        # print(f"Number of RDF triples: {document.total_triples}")
        # print(f"Number of subjects: {document.nb_subjects}")
        # print(f"Number of predicates: {document.nb_predicates}")
        # print(f"Number of objects: {document.nb_objects}")
        # print(f"Number of shared subject-object: {document.nb_shared}")

    # def _init_hdt_graph(self):
    #     """ Load an HDT file. Missing indexes are generated automatically.
    #     You can provide the index file by putting them in the same directory than the HDT file.
    #     """
    #     store = Graph(self.hdt_file)
    #
    #     # Display some metadata about the HDT document itself
    #     print(f"Number of RDF triples: {len(store)}")
    #     print(f"Number of subjects: {store.nb_subjects}")
    #     print(f"Number of predicates: {store.nb_predicates}")
    #     print(f"Number of objects: {store.nb_objects}")
    #     print(f"Number of shared subject-object: {store.nb_shared}")

    def run_query(self):
        pass
        # from rdflib import Graph
        # from rdflib_hdt import HDTStore, optimize_sparql
        #
        # # Calling this function optimizes the RDFlib SPARQL engine for HDT documents
        # optimize_sparql()
        #
        # graph = Graph(store=HDTStore("test.hdt"))
        #
        # # You can execute SPARQL queries using the regular RDFlib API
        # qres = graph.query("""
        # PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        # SELECT ?name ?friend WHERE {
        #    ?a foaf:knows ?b.
        #    ?a foaf:name ?name.
        #    ?b foaf:name ?friend.
        # }""")
        #
        # for row in qres:
        #     print(f"{row.name} knows {row.friend}")

    def get_results(self):
        pass
