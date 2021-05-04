from models.DAANJsonModel import DAAN_TYPE, ObjectType, isSceneDescription
from apis.lod.StorageLODHandler import StorageLODHandler


class DAANStorageLODHandler(StorageLODHandler):
    """ STORAGE API serves catalogue data on a URL,
    This class gets the JSON from the Direct Metadata Flex API, then uses the mapping
    information from the schema to create RDF from the JSON.
    This implementation produces RDF in the NISV scheme/model.
    """
    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def _transform_json_to_rdf(self, json_obj):
        """ Transforms the json to RDF using the schema mapping.
            This method is an override for the base class.
        """
        # get the type - series, season etc.
        cat_type = json_obj[DAAN_TYPE]

        # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
        if cat_type == ObjectType.LOGTRACKITEM.value:
            logtrack_type = json_obj["logtrack_type"]
            if not isSceneDescription(logtrack_type):
                raise ValueError(
                    "Cannot retrieve data for a logtrack item of type %s, must be of type scenedesc" % logtrack_type)
        # Note: this class is imported here, because otherwise a circular dependency is created
        from models.NISVRdfConcept import NISVRdfConcept
        return NISVRdfConcept(json_obj, cat_type, self.config)
