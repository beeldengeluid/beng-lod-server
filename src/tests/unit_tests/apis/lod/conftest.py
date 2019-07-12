import pytest

@pytest.fixture()
def o_get_record(open_file):
	""" Returns an example of XML data that can be expected."""
	return open_file(__file__, 'output_get_record.xml')

@pytest.fixture()
def o_get_schema(open_file):
	""" Returns an example version of the schema."""
	return open_file(__file__, 'output_get_schema.ttl')