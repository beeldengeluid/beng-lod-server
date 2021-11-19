from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, NamespaceManager
from rdflib.namespace import RDF, RDFS
import os


class SchemaInMemory:

    def __init__(self, profile=None):
        self.profile = profile
        self.ns = Namespace(profile['uri'])

        print(profile)
        namespace_manager = NamespaceManager(Graph())
        namespace_manager.bind(self.profile['prefix'], self.ns, override=False)

        self.graph = Graph()
        self.graph.namespace_manager = namespace_manager
        self.graph.parse(source=os.path.abspath(self.profile['schema']), format='turtle')

    def get_resource(self, class_or_prop=None, return_format='turtle'):
        """ Create a new (sub) graph to store the results in (for convenient serialization)
        """
        namespace_manager = NamespaceManager(Graph())
        namespace_manager.bind(self.profile['prefix'], self.ns, override=False)
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
                return s.toPython().replace(self.profile['uri'], '')
        return None

    def resource_name_to_html(self, schema_prefix, schema_uri, resource_name):
        """ Converts a Class or Property into the ontospy html file name,
            'e.g. Creator' -> class-nisvcreator.html
        """
        class_triple = (URIRef('{}{}'.format(schema_uri, resource_name)), RDF.type, RDFS.Class)
        prop_triple = (URIRef('{}{}'.format(schema_uri, resource_name)), RDF.type, RDF.Property)
        if class_triple in self.graph:
            return 'class-{}{}.html'.format(schema_prefix, resource_name.lower())
        elif prop_triple in self.graph:
            return 'prop-{}{}.html'.format(schema_prefix, resource_name.lower())
        return None

    def url_path_to_resource_name(self, schema_prefix, path):
        """ Converts an ontospy html file name into the right RDF resource name:
            e.g. class-nisvseason.html -> 'Season'
        """
        class_prefix = 'class-{}'.format(schema_prefix)
        prop_prefix = 'prop-{}'.format(schema_prefix)
        if path.startswith(class_prefix):
            entity_name = path[len(class_prefix):-len('.html')]
            return self.get_resource_name(entity_name=entity_name)
        elif path.startswith(prop_prefix):
            entity_name = path[len(prop_prefix):-len('.html')]
            return self.get_resource_name(entity_name=entity_name, resource_type='prop')
        return None
