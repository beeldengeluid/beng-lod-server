from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, NamespaceManager
import os


class DereferenceURIs:
    def __init__(self, schema_file=None):
        self.graph = Graph()
        print(schema_file)
        print(os.path.abspath(schema_file))
        self.graph.parse(source=os.path.abspath(schema_file), format='turtle')

    def get_resource(self, class_or_prop=None):
        nisvNs = Namespace('http://data.rdlabs.beeldengeluid.nl/schema/')
        namespace_manager = NamespaceManager(Graph())
        namespace_manager.bind('nisv', nisvNs, override=False)
        class_graph = Graph()
        class_graph.namespace_manager = namespace_manager
        s = URIRef(class_or_prop)
        for p, o in self.graph.predicate_objects(subject=s):
            class_graph.add((s, p, o))
        return class_graph.serialize(format='turtle')
