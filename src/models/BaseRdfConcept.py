import logging
from rdflib import Graph
from rdflib.namespace import SKOS, Namespace
from rdflib.plugin import PluginException
from util.APIUtil import APIUtil
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger()


class BaseRdfConcept:
    """Class to represent an NISV catalog object in RDF.
    It uses functions to create the RDF in a graph using the JSON payload from the Direct Access Metadata API.
    """

    def __init__(self, profile, model=None):
        self.profile = profile
        if "schema" not in self.profile or "mapping" not in self.profile:
            raise APIUtil.raiseDescriptiveValueError(
                "internal_server_error", "Schema or mapping file not specified"
            )
        self._model = model
        self._schema = None
        self._classes = None
        self.itemNode = None
        self.classUri = None
        self.graph = Graph(bind_namespaces="core")
        self.graph.namespace_manager.bind("skos", SKOS)
        self.graph.namespace_manager.bind("gtaa", Namespace(self._model.GTAA_NAMESPACE))

    def get_uri(self, cat_type="PROGRAM", daan_id=None):
        if daan_id is None:
            return None
        if cat_type == "LOGTRACKITEM":
            cat_type = "SCENE"
        url_parts = urlparse(self._model.NISV_DATA_NAMESPACE)
        primary_path = self._model.NISV_DATA_PREFIX
        path = "/".join([primary_path, cat_type.lower(), daan_id])
        parts = (url_parts.scheme, url_parts.netloc, path, "", "", "")
        return urlunparse(parts)

    # noinspection PyMethodMayBeStatic
    def get_gpp_link(self, metadata, cat_type, daan_id):
        """Construct a URL for the item landing page in the general public portal.
        :param metadata: JSON metadata of the item to get daan id's
        :param cat_type: the catalogue type of the item
        :param daan_id: the alphanumerical string that is the unique identifier within the catalogue.
        :returns: the contructed URL for the landing page
        Example: https://zoeken.beeldengeluid.nl/program/urn:vme:default:program:2101810040249483931
        """
        # to get the gpp link we need to find a path on the following base_url
        gpp_base_url = "https://zoeken.beeldengeluid.nl/"

        # for some items, the path depends on information of its parents.
        # get (a possibly empty) list of parents here.
        if isinstance(metadata.get("parents"), dict):
            parents = [metadata.get("parents")]
        elif isinstance(metadata.get("parents"), list):
            parents = metadata.get("parents")
        else:
            parents = []

        # now get the path to add to the gpp_base_url, set missing or invalid parts to None.
        if cat_type == "PROGRAM":
            program_urn = f"urn:vme:default:program:{daan_id}"
            path_parts = ["program", program_urn]
        elif cat_type == "SERIES":
            series_urn = f"urn:vme:default:series:{daan_id}"
            path_parts = ["series", series_urn]
        elif cat_type == "SEASON":
            season_urn = f"urn:vme:default:season:{daan_id}"

            # get urn for parent series or None
            series_ids = [
                parent.get("parent_id")
                for parent in parents
                if parent.get("parent_type") == "SERIES"
            ]
            series_id = series_ids[0] if len(series_ids) > 0 else None
            series_urn = (
                f"urn:vme:default:series:{series_id}" if series_id is not None else None
            )

            # combine the urns into a path
            path_parts = ["series", series_urn, season_urn]
        elif cat_type == "LOGTRACKITEM":
            logtrackitem_urn = f"urn:vme:default:logtrackitem:{daan_id}"

            # get urn for parent program or None
            program_ref_id = metadata.get("program_ref_id")
            program_urn = (
                f"urn:vme:default:program:{program_ref_id}"
                if program_ref_id is not None
                else None
            )
            # get urn for parent asset or None
            items_ids = [
                parent.get("parent_id")
                for parent in parents
                if parent.get("parent_type") == "ITEM"
            ]
            item_id = items_ids[0] if len(items_ids) > 0 else None
            asset_urn = (
                f"urn:vme:default:asset:{item_id}" if item_id is not None else None
            )

            # combine the urns into a path
            path_parts = [
                "program",
                program_urn,
                "asset",
                asset_urn,
                "segment",
                logtrackitem_urn,
            ]
        else:
            path_parts = []

        # combine the gpp_base_url with the path parts we derived if they are valid.
        if len(path_parts) > 0 and None not in path_parts:
            gpp_base = urlparse(gpp_base_url)
            gpp_link = urlunparse(
                (gpp_base.scheme, gpp_base.netloc, "/".join(path_parts), "", "", "")
            )
        else:
            logging.error(
                "cannot get gpp_link for daan_id '%s', cat_type '%s'. got to path parts '%s'"
                % (daan_id, cat_type, path_parts)
            )
            gpp_link = None
        return gpp_link

    def get_classes(self):
        if self._schema is not None:
            return self._schema.get_classes()
        return None

    @staticmethod
    def _get_metadata_value(metadata, metadata_field):
        """Gets the value of the metadata field from the JSON metadata.
        :param: metadata: JSON metadata
        :param: metadata_field, the name of the field to retrieve the value for.
            :returns: either a single value, a list of multiple values, or a dict.
        """
        if "," in metadata_field:
            field_parts = metadata_field.split(",")

            if type(metadata) is not list:
                value_list = [
                    metadata
                ]  # create a list as the metadata field could contain a list at some point
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
        """Serialize graph data to requested format."""
        try:
            return self.graph.serialize(
                format=return_format,
                auto_compact=True,
            )
        except PluginException:
            logger.exception("PluginException")
            raise
