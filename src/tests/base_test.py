import os

"""
Tests everything related to the validity of the application settings (settings.py)
"""


def test_settings_exist(base_file_path):
    assert os.path.exists(os.path.join(base_file_path, 'config', 'settings-example.py'))


def test_settings_valid(application_settings):
    assert 'APP_HOST' in application_settings and type(application_settings['APP_HOST']) == str  # e.g. '0.0.0.0'
    assert 'APP_PORT' in application_settings and type(application_settings['APP_PORT']) == int
    assert 'APP_VERSION' in application_settings and type(application_settings['APP_VERSION']) == str

    assert 'DEBUG' in application_settings and type(application_settings['DEBUG']) == bool

    assert 'PROFILES' in application_settings and type(application_settings['PROFILES']) == list
