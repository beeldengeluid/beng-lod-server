import logging
from rdflib import Graph
from rdflib.namespace import SKOS, Namespace
from rdflib.plugin import PluginException
from util.APIUtil import APIUtil
from urllib.parse import urlparse, urlunparse


class BaseRdfConcept:
    """ Class to represent an NISV catalog object in RDF.
        It uses functions to create the RDF in a graph using the JSON payload from the Direct Access Metadata API.
    """

    def __init__(self, profile, model=None):
        self.profile = profile
        if "schema" not in self.profile or "mapping" not in self.profile:
            raise APIUtil.raiseDescriptiveValueError('internal_server_error', 'Schema or mapping file not specified')
        self._model = model
        self._schema = None
        self._classes = None
        self.itemNode = None
        self.classUri = None
        self.graph = Graph()
        # self.graph.namespace_manager.bind(self._model.NISV_SCHEMA_PREFIX,
        #                                   Namespace(self._model.NISV_SCHEMA_NAMESPACE))
        # self.graph.namespace_manager.bind(self._model.NISV_DATA_PREFIX,
        #                                   Namespace(self._model.NISV_DATA_NAMESPACE))
        self.graph.namespace_manager.bind("skos", SKOS)
        self.graph.namespace_manager.bind("gtaa", Namespace(self._model.GTAA_NAMESPACE))
        self.graph.namespace_manager.bind("non-gtaa", Namespace(self._model.NON_GTAA_NAMESPACE))

    def get_uri(self, cat_type="PROGRAM", daan_id=None):
        if daan_id is None:
            return None
        url_parts = urlparse(self._model.NISV_DATA_NAMESPACE)
        primary_path = self._model.NISV_DATA_PREFIX
        path = '/'.join([primary_path, cat_type.lower(), daan_id])
        parts = (url_parts.scheme, url_parts.netloc, path, '', '', '')
        return urlunparse(parts)

    # noinspection PyMethodMayBeStatic
    def get_gpp_link(self, cat_type="PROGRAM", daan_id=None):
        """ Construct a URL for the item landing page in the general public portal.
        :param cat_type: the catalogue type of the item
        :param daan_id: the alphanumerical string that is the unique identifier within the catalogue.
        :returns: the contructed URL for the landing page
        Example: https://zoeken.beeldengeluid.nl/program/urn:vme:default:program:2101810040249483931
        """
        if cat_type.upper() == "SEASON":
            # TODO: fix the landing page for season (join with series)
            # example: https://zoeken.beeldengeluid.nl/
            # series/urn:vme:default:series:2101608030027704331/urn:vme:default:season:2101608040029114331
            return None
        return f'https://zoeken.beeldengeluid.nl/{cat_type.lower()}/urn:vme:default:{cat_type.lower()}:{daan_id}'

    def get_classes(self):
        if self._schema is not None:
            return self._schema.get_classes()
        return None

    # noinspection PyMethodMayBeStatic
    def _get_metadata_value(self, metadata, metadata_field):
        """ Gets the value of the metadata field from the JSON metadata.
        :param: metadata: JSON metadata
        :param: metadata_field, the name of the field to retrieve the value for.
            :returns: either a single value, or a list of multiple values
        """
        if "," in metadata_field:
            field_parts = metadata_field.split(",")

            if type(metadata) is not list:
                value_list = [metadata]  # create a list as the metadata field could contain a list at some point
            else:
                value_list = metadata

            for part in field_parts:
                part = part.strip()  # remove any whitespace
                new_value_list = []
                found = False
                for value in value_list:
                    if value:
                        if part in value:
                            found = True
                            if type(value[part]) is list:
                                new_value_list.extend(value[part])
                            else:
                                new_value_list.append(value[part])
                if not found:
                    return ""  # no value for the metadata field
                value_list = new_value_list

            return value_list
        else:
            if metadata_field in metadata:
                return metadata[metadata_field]
            else:
                return ""

    def serialize(self, return_format):
        """ Serialize graph data to requested format."""
        try:
            return self.graph.serialize(
                format=return_format,
                context=dict(self.graph.namespaces()),
                auto_compact=True
            )
        except PluginException as e:
            logging.error(str(e))
            print(e)
            raise
        except Exception as e:
            logging.error('serializeGraph => ')
            logging.error(str(e))
            print('serializeGraph => ')
            print(e)
