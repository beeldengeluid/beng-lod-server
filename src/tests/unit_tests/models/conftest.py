import pytest


@pytest.fixture()
def i_dmapi_program(load_json_file):
    """Search hit for program in flexdatastore."""
    return load_json_file(__file__, "get_dmapi_program_2101606230008608731.json")
