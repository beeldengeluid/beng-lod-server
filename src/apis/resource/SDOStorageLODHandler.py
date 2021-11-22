from models.DAANJsonModel import DAAN_TYPE, ObjectType, isSceneDescription
from apis.resource.StorageLODHandler import StorageLODHandler


class SDOStorageLODHandler(StorageLODHandler):
    """ STORAGE API serves catalogue data on a URL. This class gets the JSON from the URL,
        then uses the mapping information from the schema to create RDF from the JSON.
        This implementation produces RDF using the schema.org ontology (SDO)).
    """
    def __init__(self, config, profile):
        super().__init__(config)
        self.profile = profile

    def _transform_json_to_rdf(self, json_obj):
        self.logger.debug('Transform json to RDF (SDO)')
        """ Transforms JSON data from the flex Direct Access Metadata API to schema.org
        """
        # get the type - series, season etc.
        cat_type = json_obj[DAAN_TYPE]

        # if the type is a logtrackitem, check it is a scene description, as we can't yet handle other types
        if cat_type == ObjectType.LOGTRACKITEM.value:
            logtrack_type = json_obj["logtrack_type"]
            if not isSceneDescription(logtrack_type):
                raise ValueError(
                    f"Cannot retrieve data for a logtrack item of type {logtrack_type}. Must be of type 'scenedesc'")

        # Note that this is import is here on purpose and not at the top, to prevent circular dependency to happen
        from models.SDORdfConcept import SDORdfConcept
        return SDORdfConcept(json_obj, cat_type, self.profile)
