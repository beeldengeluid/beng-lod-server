#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import requests
from datetime import datetime
import os
import pathlib
import csv
from rdflib import Graph
from rdflib.plugin import PluginException
from urllib.error import URLError


def date_time_string():
    dts = datetime.utcnow()
    return ''.join([f'{dts.year}', f'{dts.month:02}', f'{dts.day:02}',
                    f'{dts.hour:02}', f'{dts.minute:02}', f'{dts.second:02}'])


def get_concept_uri(set_spec, c_notation):
    uri = u'http://data.beeldengeluid.nl/%s/%s.rdf' % (set_spec, c_notation)
    return uri


# def get_concept_data(uri, return_format=None):
#     graph = Graph()
#     try:
#         graph.load(uri)
#     except URLError as e:
#         return None
#     except FileNotFoundError as e:
#         return None
#
#     try:
#         return graph.serialize(format=return_format)
#     except PluginException as err:
#         return None


# def get_concept_rdf(set_spec, concept_notation, return_format):
#     uri = get_concept_uri(set_spec, concept_notation)
#     data = get_concept_data(uri, return_format)
#     if data is None:
#         return None
#     return data.decode("utf-8")  # decode, because it is binary data


def get_the_concept_data(csv_path=None):
    """ Iterate over the list of notations and get the RDF. Write to N-triples file.
    :param csv_path: the path to the csv file with the person names and notations.
    """
    with open(csv_path, encoding='utf-8') as csv_file:
        # don't set the field names and it will automatically use first line as header row
        reader = csv.DictReader(csv_file,
                                delimiter='\t',
                                fieldnames=["notation", "pref_label"],  # list of keys for the dict
                                skipinitialspace=True)

        out_fn = 'ecv_personen_all_data_%s.nt' % date_time_string()
        output_format = 'application/n-triples'
        qa_set_spec = 'gtaa'
        logging.info("Writing %s ..." % out_fn)
        with open(out_fn, 'w', encoding='utf-8') as outfile:
            for row in reader:
                try:
                    pref_label = row['pref_label']
                    notation = row['notation']
                    if notation == '':
                        continue
                    data = get_concept_rdf(set_spec=qa_set_spec,
                                           concept_notation=notation,
                                           return_format=output_format)
                    if data is None:
                        logging.debug(f'OpenSKOS returns no data for this person: {notation}: {pref_label}')
                        continue
                    outfile.write(data)
                except UnicodeDecodeError as e:
                    logging.error(str(e))


def generate_dataset():
    """ Generates the JSON-LD for one dataset. """
    g = Graph()
    return g


def generate_all_datasets():
    """ Generate the JSON-LD for all the datasets in the spreadsheet. """
    # For all rows in the spreadsheet, generate_datasets

if __name__ == '__main__':
    # set the log file
    log_dir = os.path.abspath(os.path.expanduser('~/logs'))
    logging.basicConfig(filename=os.path.join(log_dir, 'dataset_csv_to_jsonld_%s.log' % date_time_string()),
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s')

    from src.settings import Config

    # csv with dataset information
    full_path = pathlib.Path(Config['DATASETS_CSV_FILE_PATH']).as_uri()

    # generate the JSON-LD


    get_the_concept_data(csv_path=full_path)
    print("Done.")
