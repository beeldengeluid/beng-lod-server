from flask_restx import Api
from .lod.lod_api import api as lodAPI
from .lod.lod_api import get_generic

apiVersion = 'v0.2'
basePath = '/'

api = Api(version=apiVersion)

api.add_namespace(lodAPI, path='%s' % basePath)


# # # TODO: find out if this Flask extension is better suited for the LOD server:
# # # https://flask-restful.readthedocs.io/en/latest/extending.html#content-negotiation
