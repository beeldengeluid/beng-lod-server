import os
from flask import current_app, request, Response, render_template, send_from_directory
from flask_restx import Namespace, fields, Resource
from apis.lod.LODHandlerConcept import LODHandlerConcept
from apis.lod.DataCatalogLODHandler import DataCatalogLODHandler
from urllib.parse import urlparse, urlunparse

from rdflib import Graph
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph

from rdflib.namespace import RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

from pyvis.network import Network
import networkx as nx

api = Namespace('lod', description='Resources in RDF for Netherlands Institute for Sound and Vision.')

# generic response model
responseModel = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

""" --------------------------- RESOURCE ENDPOINT -------------------------- """

MIME_TYPE_JSON_LD = 'application/ld+json'
MIME_TYPE_RDF_XML = 'application/rdf+xml'
MIME_TYPE_TURTLE = 'text/turtle'
MIME_TYPE_N_TRIPLES = 'application/n-triples'
MIME_TYPE_N3 = 'text/n3'
MIME_TYPE_JSON = 'application/json'
MIME_TYPE_HTML = 'text/html'

ACCEPT_TYPES = [
    MIME_TYPE_JSON_LD,
    MIME_TYPE_RDF_XML,
    MIME_TYPE_TURTLE,
    MIME_TYPE_N_TRIPLES,
    MIME_TYPE_JSON,
    MIME_TYPE_N3,
    MIME_TYPE_HTML
]

MIME_TYPE_TO_LD = {
    MIME_TYPE_RDF_XML: 'xml',
    MIME_TYPE_JSON_LD: 'json-ld',
    MIME_TYPE_N_TRIPLES: 'nt',
    MIME_TYPE_TURTLE: 'turtle',
    MIME_TYPE_JSON: 'json-ld',
    MIME_TYPE_N3: 'n3',
    MIME_TYPE_HTML: 'turtle'
}

# TODO: make sure the schema file is downloadable in turtle
# DAAN_PROFILE = 'http://data.rdlabs.beeldengeluid.nl/schema/'
SDO_PROFILE = 'https://schema.org/'


def get_profile_by_uri(profile_uri, app_config):
    for p in app_config['PROFILES']:
        if p['uri'] == profile_uri:
            return p
    else:  # otherwise return the default profile
        return app_config['ACTIVE_PROFILE']


def rdf_to_image(rdf_string=None, rdf_format=MIME_TYPE_JSON_LD):
    """ Use Pyvis to visualize a Graph in HTML. See: https://pyvis.readthedocs.io/en/latest/index.html
    Examples VisJS: https://visjs.github.io/vis-network/examples/
    """
    g = Graph()
    g.parse(data=rdf_string, format=rdf_format)

    html_path = 'static/rdf_to_image.html'
    if os.path.isfile(html_path):
        os.remove(html_path)

    # generate a networkx multidigraph object
    mdg = rdflib_to_networkx_multidigraph(g)

    # Plot Networkx instance of RDF Graph
    pos = nx.spring_layout(mdg, scale=2)

    node_labels = get_mapping_for_schema_nodes()
    # edge_labels = get_mapping_for_schema_edges()
    # print('PRINT NETWORK EDGES')
    # for edge in mdg.edges():
    #     # check id edge has label
    #     # edge is a tuple. find out whether one of the two nodes is also in edge
    #     # replace it with get_mapping_for_schema_edges()
    #     print(edge)
    #     print(f'EDGE IN EDGE_LABELS: {edge in edge_labels}')

    # nx.draw_networkx_edge_labels(mdg, pos, edge_labels=edge_labels)
    relabeled_mdg = nx.relabel_nodes(mdg, node_labels)
    # edge_labels = nx.get_edge_attributes(mdg, 'label')
    # for label in edge_labels:
    #     print(label)

    # edge_labels = dict([((n1, n2), f'{n1}->{n2}')
    #                     for n1, n2 in mdg.edges])
    # edge_labels = {
    #     (n1, n2): f'{n1}->{n2}'
    #     for n1, n2 in mdg.edges
    # }

    # nx.draw_networkx_edge_labels(mdg, pos, edge_labels=edge_labels)

    # nx.draw_networkx(relabeled_mdg)
    # print('NETWORK NODES')
    # print(list(mdg.nodes()))
    # print('NETWORK EDGES')
    # print(list(mdg.edges()))

    # Do the pyvis shine
    net = Network(height='768px', width='1024px')
    # net.toggle_physics(status=True)
    # net.add_edge()

    # populates the nodes and edges data structures
    net.from_nx(relabeled_mdg)
    net.show_buttons(filter_=['physics'])
#     net.set_options("""
# var options = {
#   "physics": {
#     "barnesHut": {
#       "gravitationalConstant": -12300,
#       "centralGravity": 0,
#       "springLength": 55
#     },
#     "minVelocity": 0.75
#   }
# }
#         """)
    net.write_html(html_path, notebook=False)


def get_mapping_for_schema_nodes():
    """# we want different labels for the URIRef. Therefor we need acces to the schema in memory"""
    profiles = current_app.config.get('ACTIVE_PROFILE')
    sim = profiles.get('sim')
    sparql_query = '''SELECT DISTINCT ?str_uri ?uri_label \
        WHERE { ?uri rdfs:label ?uri_label FILTER(LANG(?uri_label) = 'en') BIND(STR(?uri) AS ?str_uri)} \
        '''
    mapping = {
        str(k): str(v).replace('https://schema.org/', 'schema:')
        for k, v in sim.graph.query(sparql_query)
    }
    # print('MAPPING SCHEMA CLASSES')
    # print(mapping)
    return mapping


def get_mapping_for_schema_edge_labels():
    """ Returns the edges, including the label: {(A,B):'a to b'}
    TODO: Use something like this:
    nx.draw_networkx_edge_labels(G,pos,edge_labels={('A','B'):'AB',\
    ('B','C'):'BC',('B','D'):'BD'},font_color='red')
    draw functions use the matlab library, which I uninstalled, because we use pyvis.
    So, maybe we need to add the edges and labels one by one using add_edge?
    """
    profiles = current_app.config.get('ACTIVE_PROFILE')
    sim = profiles.get('sim')
    q = prepareQuery(
        """SELECT DISTINCT ?a ?b ?prop_label
        WHERE {
          ?a ?property ?b .
          ?property rdfs:label ?prop_label
        }""",
        initNs={
            "rdf": RDF,
            "rdfs": RDFS
        }
        # ?property rdf:type/rdfs:subClassOf* rdf:Property .
        # ?property rdfs:label ?prop_label
    )
    # ?property rdfs:label ?prop_label
    for edge in sim.graph.query(q):
        print(edge)
        # print(f"{edge.s} connected to {edge.p} with edge label {edge.o}")
        # print(f"{edge.a} connected to {edge.b} with edge label {edge.property}")

    # mapping = {
    #     str(k): str(v)
    #     for k, v in sim.graph.query(sparql_query)
    # }
    # print('MAPPING SCHEMA PROPERTIES')
    # print(mapping)
    # return mapping


def get_mapping_for_schema_edges():
    """ Returns a mapping of the property URIs to the rdfs:labels for the properties. It gets these from the
    schema in memory. """
    profiles = current_app.config.get('ACTIVE_PROFILE')
    sim = profiles.get('sim')
    q = prepareQuery(
        """SELECT DISTINCT ?property ?prop_label
        WHERE { 
          ?uri ?property ?uri_label .
          ?property rdf:type/rdfs:subClassOf* rdf:Property .
          ?property rdfs:label ?prop_label
        }""",
        initNs={
            "rdf": RDF,
            "rdfs": RDFS
        }
    )
    mapping = {
        str(row.uri): str(row.uri_label)
        for row in sim.graph.query(q)
    }
    # print('MAPPING SCHEMA PROPERTIES')
    # print(mapping)
    # for triple in sim.graph:
    #     print(triple)

    return mapping


def get_lod_resource(level, identifier, mime_type, accept_profile, app_config):
    """ Generates the expected data based on the mime_type.
        It can be used by the accept-decorated methods from the resource derived class.

        :param level: meaning the catalogue type, e.g. like 'program' (default), 'series', etc.
        :param identifier: the DAAN id the resource is findable with, in combination with level
        :param mime_type: the mime_type, or serialization the resource is requested in.
        :param accept_profile: the model/schema/ontology the data is requested in.
        :param app_config: the application configuration
        :return: RDF data in a response object
    """
    """ See: https://www.w3.org/TR/dx-prof-conneg/#related-http
        NOTE: Abuse the Accept header with additional parameter:
        Example: Accept: application/ld+json; profile="http://schema.org"
    """
    profile = get_profile_by_uri(accept_profile, app_config)
    ld_format = MIME_TYPE_TO_LD.get(mime_type)

    if mime_type == MIME_TYPE_HTML:
        # for HTML view we have to apply the schema.org for better visualization results
        profile = get_profile_by_uri(SDO_PROFILE, app_config)

    resp, status_code, headers = profile['storage_handler'](app_config, profile).get_storage_record(
        level,
        identifier,
        ld_format
    )

    if mime_type == MIME_TYPE_HTML:
        get_mapping_for_schema_edge_labels()
        rdf_to_image(resp.decode("utf-8"), rdf_format=ld_format)
        return Response(response=render_template('rdf_to_image.html', level=level, identifier=identifier))

    # make sure to apply the correct mimetype for valid responses
    if status_code == 200:
        content_type = mime_type
        if headers.get('Content-Type') is not None:
            content_type = headers.get('Content-Type')
        profile_param = '='.join(['profile', '"{}"'.format(profile['schema'])])
        headers['Content-Type'] = ';'.join([content_type, profile_param])
        return Response(resp, mimetype=mime_type, headers=headers)
    return Response(resp, status_code, headers=headers)


def parse_accept_header(accept_header):
    """ Parses an Accept header for a request for RDF to the server. It returns the mime_type and profile.
    :param: accept_header: the Accept parameter from the HTTP request.
    :returns: mime_type, accept_profile. None if input parameter is missing.
    """
    # mime_type = MIME_TYPE_JSON_LD
    mime_type = MIME_TYPE_HTML
    accept_profile = None

    if accept_header is None or accept_header == '*/*':
        return mime_type, accept_profile

    if accept_header in ACCEPT_TYPES:
        return accept_header, accept_profile

    if accept_header.find(';') != -1 and accept_header.find('profile') != -1:
        temp = accept_header.split(';')
        if len(temp) == 2:
            mime_type = temp[0]

            kv = temp[1].split('=')
            if len(kv) > 1 and kv[0] == 'profile':
                accept_profile = kv[1].replace('"', '')
    return mime_type, accept_profile


def prepare_beng_uri(path):
    """ Use the domain and the path given to construct a proper Beeld en Geluid URI. """
    parts = urlparse(current_app.config['BENG_DATA_DOMAIN'])
    new_parts = (parts.scheme, parts.netloc, path, None, None, None)
    return urlunparse(new_parts)


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/<any(program, series, season, logtrackitem):cat_type>/<int:identifier>', endpoint='dereference')
class LODAPI(Resource):

    def get(self, identifier, cat_type='program'):
        """ Get the RDF for the catalogue item. """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))

        if mime_type:
            # note we need to use empty params for the UI
            return get_lod_resource(
                level=cat_type,
                identifier=identifier,
                mime_type=mime_type,
                accept_profile=accept_profile,
                app_config=current_app.config
            )
        return Response('Error: No mime type detected...')


""" --------------------------- GTAA ENDPOINT -------------------------- """


@api.route('concept/<set_code>/<notation>', endpoint='concept')
class LODConceptAPI(Resource):
    LD_TO_MIME_TYPE = {v: k for k, v in MIME_TYPE_TO_LD.items()}

    def _extractDesiredFormats(self, accept_type):
        mimetype = 'application/rdf+xml'
        if accept_type.find('rdf+xml') != -1:
            mimetype = 'application/rdf+xml'
        elif accept_type.find('json+ld') != -1:
            mimetype = 'application/ld+json'
        elif accept_type.find('json') != -1:
            mimetype = 'application/ld+json'
        elif accept_type.find('turtle') != -1:
            mimetype = 'text/turtle'
        elif accept_type.find('json') != -1:
            mimetype = 'text/n3'
        return mimetype, self.MIME_TYPE_TO_LD[mimetype]

    @api.response(404, 'Resource does not exist error')
    def get(self, set_code, notation):
        """ Get the RDF for the SKOS Concept. """
        accept_type = request.headers.get('Accept')
        user_format = request.args.get('format', None)
        mimetype, ld_format = self._extractDesiredFormats(accept_type)

        # override the accept format if the user specifies a format
        if user_format and user_format in self.LD_TO_MIME_TYPE:
            ld_format = user_format
            mimetype = self.LD_TO_MIME_TYPE[user_format]

        resp, status_code, headers = LODHandlerConcept(current_app.config).get_concept_rdf(set_code, notation,
                                                                                           ld_format)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mimetype, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


""" --------------------------- DATASETS ENDPOINTS -------------------------- """


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/dataset/<number>', endpoint='datasets')
@api.doc(params={'number': {'description': 'Enter a zero padded 4 digit integer value.', 'in': 'number'}})
class LODDatasetAPI(Resource):
    """ Serve the RDF for the dataset in the format that was requested. A dataset contains distributions.
    """

    @api.response(404, 'Resource does not exist error')
    def get(self, number=None):
        """ Get the RDF for the Dataset, including its DataDownloads.
        All triples for the Dataset and its DataDownloads are included.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))
        ld_format = MIME_TYPE_TO_LD.get(mime_type)
        dataset_uri = prepare_beng_uri(path=f'id/dataset/{number}')

        resp, status_code, headers = DataCatalogLODHandler(app_config=current_app.config
                                                           ).get_dataset(dataset_uri,
                                                                         mime_format=ld_format)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


""" --------------------------- DATACALOG ENDPOINT -------------------------- """


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/datacatalog/<number>', endpoint='data_catalogs')
@api.doc(params={'number': {'description': 'Enter a zero padded 3 digit integer value.', 'in': 'number'}})
class LODDataCatalogAPI(Resource):

    @api.response(404, 'Resource does not exist error')
    def get(self, number=None):
        """ Get the RDF for the DataCatalog, including its Datasets.
        All triples describing the DataCatalog and its Datasets are included.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))
        ld_format = MIME_TYPE_TO_LD.get(mime_type)
        data_catalog_uri = prepare_beng_uri(path=f'id/datacatalog/{number}')

        resp, status_code, headers = DataCatalogLODHandler(app_config=current_app.config
                                                           ).get_data_catalog(data_catalog_uri,
                                                                              mime_format=ld_format)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers


"""---------DataDownloads---------"""


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/datadownload/<number>', endpoint='data_downloads')
@api.doc(params={'number': {'description': 'Enter a zero padded 4 digit integer value.', 'in': 'number'}})
class LODDataDownloadAPI(Resource):

    @api.response(404, 'Resource does not exist error')
    def get(self, number=None):
        """ Get the RDF for the DataDownload.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))
        ld_format = MIME_TYPE_TO_LD.get(mime_type)
        data_download_uri = prepare_beng_uri(path=f'id/datadownload/{number}')

        resp, status_code, headers = DataCatalogLODHandler(app_config=current_app.config
                                                           ).get_data_download(data_download_uri,
                                                                               mime_format=ld_format)

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers
