import ontospy
from ontospy.ontodocs.viz.viz_html_single import HTMLVisualizer
from ontospy.ontodocs.viz.viz_html_multi import KompleteVizMultiModel


class ontodoc:
    """
    Given the bengschema.ttl ontology this class generates several visualisations for the ontology.
    Whenever the server starts this ontology documentation is re-generated.

    NB: The CLI command is:  `ontospy  gendocs --type=8 - -extra - -nobrowser - l
    ~ / PycharmProjects / beng - lod - server / resource / bengSchema.ttl`

    """

    def __init__(self, ontology_file=None, output_path=None, profile=None):
        self.graph_file = ontology_file
        self.profile = profile
        self.model = ontospy.Ontospy(self.graph_file, verbose=True)
        # self.gendocs(output_folder=output_path)
        self.complete_docs(output_folder=output_path)

        # self.test()

    def test(self):
        for c in self.model.all_classes:
            print(c)
        for p in self.model.all_properties_object:
            print(p)

        self.model.printClassTree()

    def gendocs(self, output_folder=None):
        """
        Given the model generate the visualisations.
        :param: output_folder: the location on the file system where the static ontology website can be stored.
        """
        if output_folder is not None:
            v = HTMLVisualizer(self.model)  # => instantiate the visualization object
            # v.build(output_path='templates/ontospy-viz')  # => render visualization.
            v.build(output_path=output_folder)  # => render visualization.

    def complete_docs(self, output_folder=None):
        """
        :param: output_folder: the location on the file system where the static ontology website can be stored.
        Generate the full documentation for the given model.
        :return:
        #"""
        if output_folder is not None:
            v = KompleteVizMultiModel(
                self.model,
                title=self.profile["title"]
                if "title" in self.profile
                else "Unknown schema",
                # output_path_static='/home/wmelder/PycharmProjects/beng-lod-server/src/static',
                static_url="/static/ontospy/{}/static/".format(self.profile["prefix"]),
                theme="yeti",
            )  # => instantiate the visualization object
            # attempt to put the files into the webserver directory
            # v.build(output_path='/var/www/docs')  # => render visualization.
            # v.build(output_path='docs')  # => render visualization.
            v.build(output_path=output_folder)  # => render visualization.
