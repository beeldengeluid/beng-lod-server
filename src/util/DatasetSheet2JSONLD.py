#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import os
from rdflib import Graph
from rdflib.namespace import Namespace
from rdflib import URIRef, Literal
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re

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
        row_dict = {values[0][row.index(value)]: value for value in row}
        list_of_dicts.append(row_dict)
    return list_of_dicts


def string_as_literal(value, field):
    """ Given a string value from the spreadsheet, generate a lang string Literal.
        Assume 'nl' as default language.
        Spreadsheet values can have '@nl' or '@en' at the end of the string.
        :param value: a string containing some value for a field
        :param field: the name of the field.
        :returns: a (list of) strings with lang attributes for the right fields
    """
    try:
        # check if field needs lang attribute
        if field not in ['name', 'description', 'alternateName']:
            return value
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


def get_literal_for_value(value, field):
    """ In case the value is a list, it is processed multiple times.
    :param value: from the spreadsheet cell
    :param field: the header for the spreadsheet column
    :returns: list of literals for al the values in the string
    """
    list_values = value.split('\n')
    return [
        string_as_literal(value, field)
        for value in list_values
        if value != ''
    ]


class DatasetSheet2JSONLD:
    """ Connect to a spreadsheet using Google Sheet API.
        Get the Datacatalog and Dataset information and make a nice JSON-LD document from this.
        TODO: For front-end developers Graph based data can be difficult, therefore the class also needs to
        provide a proper tree structured JSON file.
    """

    def __init__(self, config=None):
        assert config is not None, 'DatasetSheet2JSONLD needs configuration.'
        self._service_account_file = config.SERVICE_ACCOUNT_FILE
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
        self.write_json_ld()
        self.write_turtle()

    def write_turtle(self, json_ld_file='graph_as_string.ttl'):
        """ Serialize the data catalog to a Turtle file"""
        with open(json_ld_file, 'w') as f:
            f.write(self.graph_as_string(serialization_format='turtle'))

    def write_json_ld(self, json_ld_file='graph_as_string.jsonld'):
        """ Serialize the data catalog to a JSON-LD file"""
        with open(json_ld_file, 'w') as f:
            f.write(self.graph_as_string())

    def graph_as_string(self, serialization_format='json-ld'):
        return self._data_catalog.serialize(format=serialization_format,
                                            context=dict(self._data_catalog.namespaces()),
                                            auto_compact=True).decode("utf-8")

    def list_of_dict_to_graph(self, list_of_dict):
        """ Generate triples and add to the data catalog graph. """
        for row in list_of_dict:
            item_id = URIRef(row.get('@id'))
            [
                self._data_catalog.add((item_id, URIRef(f'{SDO}{key}'), get_literal_for_value(value, key)))
                for key, value in row.items()
                if (item_id is not None) and key != '@id'
            ]

    def _init_sheets_api(self):
        """ Initializes the sheets api, preparing it ot read data.
        """
        credentials = service_account.Credentials.from_service_account_file(self._service_account_file,
                                                                            scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        self._sheet = service.spreadsheets()

    def _init_namespaces(self):
        """ Init the datacatalog Graph with the right namespaces.
        """
        # self._data_catalog.namespace_manager.bind('schema', SDO)
        self._data_catalog.bind('schema', SDO)
        print(dict(self._data_catalog.namespaces()))

    def _init_data_catalog(self):
        """ Read the values from a Google spreadsheet. Convert every row into a dict using the
            header row for the keys. From the dict generate triples and add these to the graph.
        """
        logging.debug('Init data catalog.')
        data_catalog_range = 'DataCatalog!A1:E'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=data_catalog_range).execute()
        data_catalog_list = values_to_dict(result.get('values', []))
        self.list_of_dict_to_graph(data_catalog_list)

    def _init_datasets(self):
        """ Read the dataset information from the spreadsheet and load into a dict.
        """
        logging.debug('Init datasets.')
        dataset_range = 'Dataset!A1:T'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=dataset_range).execute()
        dataset_list = values_to_dict(result.get('values', []))
        self.list_of_dict_to_graph(dataset_list)

    def _init_data_downloads(self):
        """ Read the DataDownload information from the spreadsheet and load into a dict.
        """
        logging.debug('Init distribution/data downloads.')
        distribution_range = 'Distribution!A1:J'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=distribution_range).execute()
        distribution_list = values_to_dict(result.get('values', []))
        self.list_of_dict_to_graph(distribution_list)

    def _init_organization(self):
        """ Read the organization information from the spreadsheet. """
        logging.debug('Init organization.')
        organization_range = 'Organization!B4:E'
        result = self._sheet.values().get(spreadsheetId=self._odl_spreadsheet_id,
                                          range=organization_range).execute()
        organization_list = values_to_dict(result.get('values', []))
        self.list_of_dict_to_graph(organization_list)

    def query(self, query=None):
        """ run a query against the data catalog graph."""


if __name__ == '__main__':
    # set the log file
    log_dir = os.path.abspath(os.path.expanduser('~/logs'))
    logging.basicConfig(filename=os.path.join(log_dir, 'dataset_csv_to_jsonld_%s.log' % date_time_string()),
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s')

    from src.settings import Config

    s2j = DatasetSheet2JSONLD(config=Config)

    # csv with dataset information
    # full_path = pathlib.Path(Config['DATASETS_CSV_FILE_PATH']).as_uri()

    # generate the JSON-LD

    # get_the_concept_data(csv_path=full_path)
    print("Done.")
