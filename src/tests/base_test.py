import os

"""
Tests everything related to the validity of the application settings (settings.py)
"""

def test_settings_exist(base_file_path):
	assert os.path.exists(os.path.join(base_file_path, 'settings.py'))

def test_settings_valid(application_settings):
	assert 'APP_HOST' in application_settings and type(application_settings['APP_HOST']) == str #e.g. '0.0.0.0'
	assert 'APP_PORT' in application_settings and type(application_settings['APP_PORT']) == int
	assert 'APP_VERSION' in application_settings and type(application_settings['APP_VERSION']) == str

	assert 'DEBUG' in application_settings and type(application_settings['DEBUG']) == bool

	assert 'OAI_BASE_URL' in application_settings and type(application_settings['OAI_BASE_URL']) == str
	assert 'SCHEMA_FILE' in application_settings and type(application_settings['SCHEMA_FILE']) == str
	assert 'MAPPING_FILE' in application_settings and type(application_settings['MAPPING_FILE']) == str