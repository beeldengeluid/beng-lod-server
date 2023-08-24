import pytest


@pytest.fixture()
def i_dmapi_program(load_json_file):
    """Search hit for program in flexdatastore."""
    return load_json_file(__file__, "get_dmapi_program_2101606230008608731.json")


@pytest.fixture()
def payload_program_2101606230008608731_json(load_json_file):
    """Returns example of flex data store JSON for a program."""
    return load_json_file(__file__, "payload_program_2101606230008608731.json")


@pytest.fixture()
def payload_series_2101608030022634031_json(load_json_file):
    """Returns example of flex data store JSON for a program."""
    return load_json_file(__file__, "payload_series_2101608030022634031.json")
