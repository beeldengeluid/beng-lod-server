from util.base_util import validate_config

"""
Tests everything related to the validity of the application settings (config/config.yml)
"""


# validate the config.yml
def test_settings_valid(application_settings):
    config_valid, returned_error = validate_config(application_settings)
    assert False if returned_error else config_valid
