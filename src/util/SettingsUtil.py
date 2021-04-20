import os

def getBasePath():
    """Gets the base path of the application"""
    pathElements = __file__.split(os.sep)
    reversePathElements = __file__.split(os.sep)[::-1]
    basePath = os.sep.join(pathElements[:-reversePathElements.index("beng-lod-server")])
    return basePath
