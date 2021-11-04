import pytest
import sys
from mockito import when, unstub
from apis.resource.SDOStorageLODHandler import SDOStorageLODHandler
from apis.concept.LODHandlerConcept import LODHandlerConcept
from util.APIUtil import APIUtil


""" ------------------------ fetchDocument -----------------------"""

DUMMY_SET = "dummy-set"
DUMMY_NOTATION = "dummy-notation"
SDO_PROFILE = 'https://schema.org/'


# def test_get_program(application_settings, url):
#     try:
#         sdo_handler = SDOStorageLODHandler(profile=SDO_PROFILE, config=application_settings)
#         when(SDOStorageLODHandler)._get_json_from_storage(url).thenReturn(json_from_file)

#         sdo_handler.get_storage_record(DUMMY_SET, DUMMY_NOTATION).thenReturn(concept_uri)
#         json_data = self._get_json_from_storage(url)

#     finally:
#         unstub()

