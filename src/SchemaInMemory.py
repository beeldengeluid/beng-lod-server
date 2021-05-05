from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, NamespaceManager
from rdflib.namespace import RDF, RDFS
import os


class SchemaInMemory:

    def __init__(self, schema_file=None):
        nisv_ns = Namespace('http://data.rdlabs.beeldengeluid.nl/schema/')
        namespace_manager = NamespaceManager(Graph())
        namespace_manager.bind('nisv', nisv_ns, override=False)
        self.graph = Graph()
        self.graph.namespace_manager = namespace_manager
        print(os.path.abspath(schema_file))
        self.graph.parse(source=os.path.abspath(schema_file), format='turtle')

    def get_resource(self, class_or_prop=None, return_format='turtle'):
        nisv_ns = Namespace('http://data.rdlabs.beeldengeluid.nl/schema/')
        namespace_manager = NamespaceManager(Graph())
        namespace_manager.bind('nisv', nisv_ns, override=False)
        class_graph = Graph()
        class_graph.namespace_manager = namespace_manager
        s = URIRef(class_or_prop)
        for p, o in self.graph.predicate_objects(subject=s):
            class_graph.add((s, p, o))
        return class_graph.serialize(format=return_format)

    def get_resource_name(self, entity_name=None, resource_type=None):
        object_type = RDFS.Class
        if resource_type == 'prop':
            object_type = RDF.Property
        for s in self.graph.subjects(RDF.type, object_type):
            if s.toPython().lower().endswith(entity_name):
                return s.toPython().replace('http://data.rdlabs.beeldengeluid.nl/schema/', '')
        return None

    #converts a Class or Property into the ontospy html file name 'e.g. Creator' -> class-nisvcreator.html
    def resource_name_to_html(self, schema_prefix, resource_name):
        class_triple = (URIRef('{}/{}'.format(schema_prefix, resource_name)), RDF.type, RDFS.Class)
        prop_triple = (URIRef('{}/{}'.format(schema_prefix, resource_name)), RDF.type, RDF.Property)
        if class_triple in self.graph:
            return 'class-nisv{}.html'.format(resource_name.lower())
        elif prop_triple in self.graph:
            return 'prop-nisv{}.html'.format(resource_name.lower())
        return None

    #converts an ontospy html file name into the right RDF resource name: e.g. class-nisvseason.html -> 'Season'
    def url_path_to_resource_name(self, path):
        if path.startswith('class-nisv'):
            entity_name = path[10:-5]
            return self.get_resource_name(entity_name=entity_name)
        elif path.startswith('prop-nisv'):
            entity_name = path[9:-5]
            return self.get_resource_name(entity_name=entity_name, resource_type='prop')
        return None
