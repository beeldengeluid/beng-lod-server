from flask_restx import Api
from .lod.lod_api import api as lodAPI

apiVersion = 'v0.3'
basePath = '/'

api = Api(version=apiVersion)

api.add_namespace(lodAPI, path='%s' % basePath)


# # # TODO: find out if this Flask extension is better suited for the LOD server:
# # # https://flask-restful.readthedocs.io/en/latest/extending.html#content-negotiation
