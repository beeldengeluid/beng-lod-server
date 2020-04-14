import ontospy
from ontospy.ontodocs.viz.viz_html_single import *
from ontospy.ontodocs.viz.viz_html_multi import *


class ontodoc:
    """
    Given the bengschema.ttl ontology this class generates several visualisations for the ontology.
    Whenever the server starts this ontology documentation is re-generated.

    NB: The CLI command is:  `ontospy  gendocs --type=8 - -extra - -nobrowser - l
    ~ / PycharmProjects / beng - lod - server / resource / bengSchema.ttl`

    """

    def __init__(self, ontology_file=None):
        self.graph_file = ontology_file
        self.model = ontospy.Ontospy(self.graph_file, verbose=True)
        # self.gendocs()
        self.complete_docs()

        # self.test()

    def test(self):
        for c in self.model.all_classes:
            print(c)
        for p in self.model.all_properties_object:
            print(p)

        self.model.printClassTree()

    def gendocs(self):
        """
        Given the model generate the visualisations.
        """
        v = HTMLVisualizer(self.model)  # => instantiate the visualization object
        v.build(output_path='templates/ontospy-viz')  # => render visualization.

    def complete_docs(self):
        """
        Generate the full documentation for the given model.
        :return:
        # """
        # v = KompleteViz(self.model,
        #                 title='Ontology for NISV Catalogue')  # => instantiate the visualization object
        # v.build(output_path='templates/docs')  # => render visualization.

        # v = KompleteVizMultiModel(self.model,
        #                           title='Ontology for NISV Catalogue',
        #                           output_path_static='/home/wmelder/PycharmProjects/beng-lod-server/src/static',
        #                           static_url='static/',
        #                           theme='yeti')  # => instantiate the visualization object
        # v.build(output_path='templates/docs')  # => render visualization.

        v = KompleteVizMultiModel(self.model,
                                  title='Ontology for NISV Catalogue',
                                  # output_path_static='/home/wmelder/PycharmProjects/beng-lod-server/src/static',
                                  # static_url='static/',
                                  theme='yeti')  # => instantiate the visualization object
        # attempt to put the files into the webserver directory
        # v.build(output_path='/var/www/docs')  # => render visualization.
        v.build(output_path='docs')  # => render visualization.