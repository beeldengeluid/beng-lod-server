import pytest
import os

@pytest.fixture()
def o_get_record(open_file):
	""" Returns an example of XML data that can be expected."""
	return open_file(__file__, 'output_get_record.xml')

@pytest.fixture()
def o_get_schema(open_file):
	""" Returns an example version of the schema."""
	return open_file(__file__, 'output_get_schema.ttl')

@pytest.fixture()
def get_concept_rdf_url():
	""" Returns a URI for a local file containing the RDF/XML for a SKOS concept."""
	def prepare_uri(path, fn):
		local_path = os.path.join(os.path.dirname(path), fn)
		if os.path.exists(local_path):
			return ''.join(['file://',  local_path])
		return None
	return prepare_uri(__file__, 'output_get_concept_rdf.xml')

@pytest.fixture()
def get_record_xml_local_uri():
	""" Returns a URI for a local file containing XML with catalogue data."""
	def prepare_uri(path, fn):
		local_path = os.path.join(os.path.dirname(path), fn)
		if os.path.exists(local_path):
			return ''.join(['file://',  local_path])
		return None
	return prepare_uri(__file__, 'output_get_record.xml')

# @pytest.fixture()
# def o_get_elementree_from_url(etree_parse_doc):
# 	""" Returns an example of XML data that can be expected."""
# 	return etree_parse_doc(__file__, 'output_get_record.xml')