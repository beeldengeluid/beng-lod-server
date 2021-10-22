#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import os
from rdflib import Graph
from rdflib.namespace import Namespace, RDF
from rdflib import URIRef, Literal
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SDO = Namespace('https://schema.org/')


def date_time_string():
    dts = datetime.utcnow()
    return ''.join([f'{dts.year}', f'{dts.month:02}', f'{dts.day:02}',
                    f'{dts.hour:02}', f'{dts.minute:02}', f'{dts.second:02}'])


def values_to_dict(values):
    """ Each row from the spreadsheet is converted to a dict using the first row as the keys.
    :param values: a list of lists containing the values of a spreadsheet loaded with the sheets api.
        The first row is considered to contain the header information.
    :returns: a list of dicts.
    """
    list_of_dicts = []
    # build a dict for each row
    for row in values[1:]:
        # use the header row for the keys
        row_dict = {values[0][index]: value for index, value in enumerate(row)}
        list_of_dicts.append(row_dict)
    return list_of_dicts


def string_as_uri(value, field):
    """ Given a string from the spreadsheet, generate a URIRef. The field is used to determine
    whether a URI is required.
    :returns: a URI, or None when the value can be processed as a Literal.
    """
    if field in ['mainEntityOfPage', 'includedInDataCatalog', 'distribution', 'contentUrl',
                 'license', 'usageInfo', 'creator', 'publisher', 'dataset', 'sameAs']:
        return URIRef(value)
    return None


def string_as_literal(value, field):
    """ Given a string value from the spreadsheet, generate a lang string Literal.
        Assume 'nl' as default language. The field is used to determine if lang string is needed.
        Spreadsheet values can have '@nl' or '@en' at the end of the string.
        :param value: a string containing some value for a field
        :param field: the name of the field.
        :returns: a (list of) strings with lang attributes for the right fields
    """
    try:
        # check if field needs lang attribute
        if field not in ['name', 'description', 'alternateName']:
            return Literal(value)
        pattern = r'^(?P<string_part>.+)@((?P<lang_part>.{2})){0,1}$'
        lang_string_pattern = re.compile(pattern, flags=re.IGNORECASE)
        result = re.match(lang_string_pattern, value)
        if result is None:
            return Literal(value, lang='nl')
        else:
            string_value = result.group('string_part')
            lang_value = result.group('lang_part')
            return Literal(string_value, lang=lang_value)
    except Exception as e:
        logging.error(str(e))


def get_object_for_value(value, field):
    """ Value is processed: a URI is produced when applicable and a Literal otherwise.
    In case the value is a list, it is processed multiple times.
    :param value: from the spreadsheet cell
    :param field: the header for the spreadsheet column
    :returns: list of objects for al the values in the value
    """
    list_values = value.splitlines()
    return [
        string_as_uri(value, field) if (string_as_uri(value, field) is not None) else string_as_literal(value, field)
        for value in list_values
        if value != ''
    ]


class DatasetSheetImporter:
    """ Connect to a spreadsheet using Google Sheet API.
    Get the DataCatalog, Dataset, DataDownload and Organization information and put it in a Graph.
    Serialize the graph to a nice file.
    """

    def __init__(self, config=None):
        assert config is not None, 'DatasetSheetImporter needs configuration.'
        # slightly difficult attempt to get the absolute path, instead of the relative path in the settings
        import inspect
        path_settings_file = Path(inspect.getfile(config))
        path_dir_settings_file = path_settings_file.parent
        self._service_account_file = str(path_dir_settings_file.joinpath(config.SERVICE_ACCOUNT_FILE))
        self._service_account_id = config.SERVICE_ACCOUNT_ID
        self._odl_spreadsheet_id = config.ODL_SPREADSHEET_ID
        self._sheet = None
        self._init_sheets_api()
        self._data_catalog = Graph()
        self._init_namespaces()
        self._init_data_catalog()
        self._init_datasets()
        self._init_organization()
        self._init_data_downloads()

    def write_data_catalog_to_file(self):
        """ First check whether the file already exists. If not create one. Otherwise do nothing."""
        json_ld_data_catalog_file = 'graph_as_string.jsonld'
        if not os.path.exists(json_ld_data_catalog_file):
            self.write_json_ld(json_ld_file=json_ld_data_catalog_file)
        turtle_data_catalog_file = 'graph_as_string.ttl'
        if not os.path.exists(turtle_data_catalog_file):
            self.write_turtle(turtle_file=turtle_data_catalog_file)

    def write_turtle(self, turtle_file=None):
        """ Serialize the whole data catalog Graph to a Turtle file"""
        if turtle_file is not None:
            self.graph_to_file(destination=turtle_file, serialization_format='turtle')

    def write_json_ld(self, json_ld_file=None):
        """ Serialize the whole data catalog Graph to a JSON-LD file.
        """
        if json_ld_file is not None:
            self.graph_to_file(destination=json_ld_file)

    def graph_to_file(self, serialization_format='json-ld', destination=None):
        """ Uses the graph's serialize method to write to file.
        Note that when destination is None the serialize method returns a string or bytes.
        """
        self._data_catalog.serialize(destination=destination,
                                     format=serialization_format,
                                     context=dict(self._data_catalog.namespaces()),
                                     encoding='utf-8',
                                     auto_compact=True)

    def list_of_dict_to_graph(self, list_of_dict):
        """ Generate triples and add to the data catalog graph.
        Processing: all the lists from the spreadsheet, all cells from each row, all lines in a cell.
        """
        for row in list_of_dict:
            item_id = URIRef(row.get('@id'))
            for key, value in row.items():
                if (item_id is not None) and key != '@id':
                    for obj in get_object_for_value(value, key):
                        self._data_catalog.add((item_id, URIRef(f'{SDO}{key}'), obj))

    def _init_sheets_api(self):
        """ Initializes the sheets api, preparing it ot read data.
        """
        credentials = service_account.Credentials.from_service_account_file(self._service_account_file,
                                                                            scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        self._sheet = service.spreadsheets()

    def _init_namespaces(self):
        """ Init the data catalog Graph with the right namespaces.
        """
        self._data_catalog.bind('sdo', SDO)

    def _init_data_catalog(self):
        """ Read the values from a Google spreadsheet. Convert every row into a dict using the
            header row for the keys. From the dict generate triples and add these to the graph.
        """
        logging.debug('Init data catalog.')
        data_catalog_range = 'DataCatalog!A1:E'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=data_catalog_range).execute()
        data_catalog_list = values_to_dict(result.get('values', []))

        # add the schema:DataCatalog type to the graph
        for row in data_catalog_list:
            item_id = URIRef(row.get('@id'))
            self._data_catalog.add((item_id, URIRef(f'{RDF}type'), URIRef(f'{SDO}DataCatalog')))

        # add all the other properties
        self.list_of_dict_to_graph(data_catalog_list)

    def _init_datasets(self):
        """ Read the dataset information from the spreadsheet and load into a dict.
            A Dataset can be the object of a schema:dataset property of the schema:DataCatalog.
            It has the property schema:includedInDataCatalog, that lists the data catalog that it is part of.
        """
        logging.debug('Init datasets.')
        dataset_range = 'Dataset!A1:T'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=dataset_range).execute()
        dataset_list = values_to_dict(result.get('values', []))

        # add a schema:Dataset type for every row
        for row in dataset_list:
            item_id = URIRef(row.get('@id'))
            self._data_catalog.add((item_id, URIRef(f'{RDF}type'), URIRef(f'{SDO}Dataset')))

            # multiple DataCatalog are possible, so add a schema:dataset for each.
            included_in_data_catalog = row.get('includedInDataCatalog')
            if included_in_data_catalog is not None:
                list_of_data_catalogs = included_in_data_catalog.splitlines()
                for data_catalog in list_of_data_catalogs:
                    data_catalog_id = URIRef(data_catalog)
                    self._data_catalog.add((data_catalog_id, URIRef(f'{SDO}dataset'), item_id))

        # now add the properties
        self.list_of_dict_to_graph(dataset_list)

    def _init_data_downloads(self):
        """ Read the DataDownload information from the spreadsheet and load into a dict.
            Every DataDownload can be used as object in a schema:distribution property for a schema:Dataset.
            The property
        """
        logging.debug('Init distribution/data downloads.')
        distribution_range = 'Distribution!A1:J'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=distribution_range).execute()
        distribution_list = values_to_dict(result.get('values', []))

        # add a schema:DataDownload type for every row
        for row in distribution_list:
            item_id = URIRef(row.get('@id'))
            self._data_catalog.add((item_id, URIRef(f'{RDF}type'), URIRef(f'{SDO}DataDownload')))

        # add the rest of the properties
        self.list_of_dict_to_graph(distribution_list)

    def _init_organization(self):
        """ Read the organization information from the spreadsheet. """
        logging.debug('Init organization.')
        organization_range = 'Organization!B4:E'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=organization_range).execute()
        organization_list = values_to_dict(result.get('values', []))

        # add a schema:Organization type
        for row in organization_list:
            item_id = URIRef(row.get('@id'))
            self._data_catalog.add((item_id, URIRef(f'{RDF}type'), URIRef(f'{SDO}Organization')))

        # add the properties for Organization
        self.list_of_dict_to_graph(organization_list)

    def query(self, query=None):
        """ run a query against the data catalog graph."""


def init_logging():
    log_dir = Path('~/logs').expanduser()
    if not log_dir.is_dir():
        log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=os.path.join(log_dir, 'dataset_sheet_importer_%s.log' % date_time_string()),
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s')


if __name__ == '__main__':
    init_logging()
    # log_dir = Path('~/logs').expanduser()
    # if not log_dir.is_dir():
    #     log_dir.mkdir(parents=True, exist_ok=True)
    # logging.basicConfig(filename=os.path.join(log_dir, 'dataset_sheet_importer_%s.log' % date_time_string()),
    #                     level=logging.DEBUG,
    #                     format='%(asctime)s %(levelname)s: %(message)s')

    # this does not work, the settings are not on the path, src.settings works on Windows apparently
    from config.settings import Config
    s2j = DatasetSheetImporter(config=Config)
    s2j.write_data_catalog_to_file()

    print("Done.")
