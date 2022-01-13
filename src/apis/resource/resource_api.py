import logging
from flask import current_app, request, Response, render_template, send_from_directory
from flask_restx import Namespace, Resource
from apis.mime_type_util import parse_accept_header, MimeType, get_profile_by_uri
import requests
from requests.exceptions import ConnectionError
from urllib.parse import urlparse, urlunparse
from util.APIUtil import APIUtil

from rdflib import Graph
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph

from rdflib.namespace import RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

from pyvis.network import Network
import networkx as nx
import os

api = Namespace('resource', description='Resources in RDF for Netherlands Institute for Sound and Vision.')

SDO_PROFILE = 'https://schema.org/'


def rdf_to_image(rdf_string=None, rdf_format=MimeType.JSON_LD):
    """ Use Pyvis to visualize a Graph in HTML. See: https://pyvis.readthedocs.io/en/latest/index.html
    Examples VisJS: https://visjs.github.io/vis-network/examples/
    """
    g = Graph()
    g.parse(data=rdf_string, format=rdf_format.value)

    html_path = 'static/rdf_to_image.html'
    if os.path.isfile(html_path):
        os.remove(html_path)

    # generate a networkx multidigraph object
    mdg = rdflib_to_networkx_multidigraph(g)

    # Plot Networkx instance of RDF Graph
    pos = nx.spring_layout(mdg, scale=2)

    node_labels = get_mapping_for_schema_nodes()
    edge_labels = get_mapping_for_schema_edge_labels()

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
    net.toggle_physics(status=True)
    # net.add_edge()

    # populates the nodes and edges data structures
    net.from_nx(relabeled_mdg)
    net.show_buttons(filter_=['physics'])
    net.set_options("""
var options = {
  "physics": {
    "barnesHut": {
      "springLength": 135
    },
    "minVelocity": 0.75
  }
}
        """)
    net.write_html(html_path, notebook=False)


def get_mapping_for_schema_nodes():
    """ Return different labels for the URIRefs. Access the schema in memory to acquire these. """
    profiles = current_app.config.get('ACTIVE_PROFILE')
    sim = profiles.get('sim')
    sparql_query = '''SELECT DISTINCT ?str_uri ?uri_label \
        WHERE { ?uri rdfs:label ?uri_label FILTER(LANG(?uri_label) = 'en') BIND(STR(?uri) AS ?str_uri)} \
        '''
    mapping = {
        str(k): str(v).replace('https://schema.org/', 'sdo:')
        for k, v in sim.graph.query(sparql_query)
    }
    print('MAPPING SCHEMA CLASSES')
    print(mapping)
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

    mapping = {
        str(k): str(v)
        for k, v in sim.graph.query(q)
    }
    print('MAPPING SCHEMA PROPERTIES')
    print(mapping)
    return mapping


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
        :param level: meaning the catalogue type: 'program' (default), 'series', 'season', 'scene'.
        :param identifier: the DAAN id.
        :param mime_type: the mime_type, or serialization the resource is requested in.
        :param accept_profile: the profile (or model/schema/ontology) the data is requested in. \
            See: https://www.w3.org/TR/dx-prof-conneg/#related-http
            Example: Accept: application/ld+json; profile="http://schema.org"
        :param app_config: the application configuration
        :return: RDF data in a response object
    """
    mt = None
    try:
        mt = MimeType(mime_type)
    except ValueError as e:
        mt = MimeType.JSON_LD

    profile = get_profile_by_uri(accept_profile, app_config)

    if mime_type == MimeType.HTML:
        # for HTML view we have to apply the schema.org for better visualization results
        profile = get_profile_by_uri(SDO_PROFILE, app_config)
        print(profile)
        resp, status_code, headers = profile['storage_handler'](app_config, profile).get_storage_record(
            level,
            identifier,
            MimeType.JSON_LD.to_ld_format()     # need to change the mimetype to be able to get the data
        )
        # now draw the graph
        # get_mapping_for_schema_edge_labels()
        rdf_to_image(resp)
        return Response(response=render_template('rdf_to_image.html', level=level, identifier=identifier))
    else:
        print(profile)
        resp, status_code, headers = profile['storage_handler'](app_config, profile).get_storage_record(
            level,
            identifier,
            mt.to_ld_format()
        )

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            content_type = mt.value
            if headers.get('Content-Type') is not None:
                content_type = headers.get('Content-Type')
            profile_param = '='.join(['profile', '"{}"'.format(profile['schema'])])
            headers['Content-Type'] = ';'.join([content_type, profile_param])
            return Response(resp, mimetype=mt.value, headers=headers)
        return Response(resp, status_code, headers=headers)


def is_public_resource(resource_url):
    """ Checks whether the resource is allowed public access by firing a query to the public sparql endpoint.
    :param resource_url: the resource to be checked.
    :return True (yes, public access allowed), False (no, not allowed to dereference)
    """
    try:
        # get the SPARQL endpoint from the config
        sparql_endpoint = current_app.config.get('SPARQL_ENDPOINT')
        query_ask = 'ASK {<%s> ?p ?o . }' % resource_url

        # prepare and get the data from the triple store
        resp = requests.get(sparql_endpoint, params={'query': query_ask, 'format': 'json'})
        assert resp.status_code == 200, 'ASK request to sparql server was not successful.'

        return resp.json().get('boolean') is True

    except ConnectionError as e:
        print(str(e))
    except AssertionError as e:
        print(str(e))
    except Exception as e:
        print(str(e))


def prepare_lod_resource_uri(level, identifier):
    """ Constructs valid url using the data domain, the level (cat type) and the identifier:
            {Beng data domain}/id/{cat_type}>/{identifier}
    :param level: the cat type
    :param identifier: the DAAN id
    :returns: a proper URI as it should be listed in the LOD server.
    """
    url_parts = urlparse(str(current_app.config.get('BENG_DATA_DOMAIN')))
    if url_parts.netloc is not None:
        path = '/'.join(['id', level, str(identifier)])
        parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
        return urlunparse(parts)
    else:
        return None


@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/<any(program, series, season, scene):cat_type>/<int:identifier>', endpoint='dereference')
class ResourceAPI(Resource):

    def get(self, identifier, cat_type='program'):
        logger = logging.getLogger(current_app.config['LOG_NAME'])
        """ Get the RDF for the catalogue item. """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))

        lod_url = prepare_lod_resource_uri(cat_type, identifier)

        # only registered user can access all items
        auth_user = current_app.config.get('AUTH_USER')
        auth_pass = current_app.config.get('AUTH_PASSWORD')
        auth = request.authorization
        if auth is not None and auth.type == 'basic' and auth.username == auth_user and auth.password == auth_pass:
            # no restrictions, bypass the check
            # logger.debug(request.authorization)
            pass
        else:
            # NOTE: this else clause is only there so we can download as lod-importer, but nobody else can.
            if not is_public_resource(resource_url=lod_url):
                return APIUtil.toErrorResponse('access_denied', 'The resource can not be dereferenced.')

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
