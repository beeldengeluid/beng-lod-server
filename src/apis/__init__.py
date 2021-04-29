from flask_restx import Api
from .lod.lod_api import api as lodAPI
from .lod.lod_api import get_generic

apiVersion = 'v0.2'
basePath = '/'

api = Api(version=apiVersion)

api.add_namespace(lodAPI, path='%s' % basePath)


# # TODO: find out if this Flask extension is better suited for the LOD server:
# # https://flask-restful.readthedocs.io/en/latest/extending.html#content-negotiation

# NOTE: These representations are only here to provide the swagger UI with proper Accept/Content types
# @api.representation('application/json+ld')
# def output_json_ld(data, code, headers=None):
#     return get_generic(data=data, code=code, headers=headers)
#
#
# @api.representation('application/rdf+xml')
# def output_rdf_xml(data, code, headers=None):
#     # return get_generic(request.get('level'), request.get('identifier'))
#     return get_generic(data, code, headers=None)
#
#
# @api.representation('application/n-triples')
# def output_n_triples(data, code, headers=None):
#     return get_generic(data, code, headers=None)
#
#
# @api.representation('text/turtle')
# def output_turtle(data, code, headers=None):
#     return get_generic(data, code, headers=None)
#
#
# @api.representation('text/html')
# def output_html(data, code, headers=None):
#     return get_generic(data, code, headers=None)
