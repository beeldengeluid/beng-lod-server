import pytest

@pytest.fixture()
def o_get_record(open_file):
	return open_file(__file__, 'output_get_record.xml')

@pytest.fixture()
def o_get_schema(open_file):
	return open_file(__file__, 'output_get_schema.ttl')