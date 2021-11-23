import os
from util.base_util import validate_config

"""
Tests everything related to the validity of the application settings (settings.py)
"""

def test_settings_exist(base_file_path):
    assert os.path.exists(os.path.join(base_file_path, 'config', 'settings_example.py'))

def test_settings_valid(application_settings):
    assert validate_config(application_settings)