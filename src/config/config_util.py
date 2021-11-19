import logging
import git
from pathlib import Path

def get_git_root():
    git_repo = git.Repo('.', search_parent_directories=True)
    return git_repo.git.rev_parse("--show-toplevel")

def config_absolute_paths(app):
    """ Some settings are relative paths. Not-absolute paths in the settings file are relative
    to the /src folder in the repo. Make these absolute or unittests will fail. """
    profile_schema_path = app.config['ACTIVE_PROFILE'].get('schema')
    src_path = Path(get_git_root()).joinpath('src')
    if profile_schema_path is not None and not Path(profile_schema_path).is_absolute():
        try:
            abs_schema_path = src_path.joinpath(profile_schema_path).resolve(strict=True)
            app.config['ACTIVE_PROFILE']['schema'] = abs_schema_path
        except FileNotFoundError as e:
            logging.error(str(e), 'Active profile schema file path could not be made absolute. '
                          'Prepare for things to go wrong in unittests.')

    profile_mapping_path = app.config['ACTIVE_PROFILE'].get('mapping')
    if profile_mapping_path is not None and not Path(profile_mapping_path).is_absolute():
        try:
            abs_mapping_path = src_path.joinpath(profile_mapping_path).resolve(strict=True)
            app.config['ACTIVE_PROFILE']['mapping'] = abs_mapping_path
        except FileNotFoundError as e:
            logging.error(str(e), 'Active profile mapping file path could not be made absolute. '
                          'Prepare for things to go wrong in unittests.')

    profile_ob_links_path = app.config['ACTIVE_PROFILE'].get('ob_links')
    if profile_ob_links_path is not None and not Path(profile_ob_links_path).is_absolute():
        try:
            abs_oblinks_path = src_path.joinpath(profile_ob_links_path).resolve(strict=True)
            app.config['ACTIVE_PROFILE']['ob_links'] = abs_oblinks_path
        except FileNotFoundError as e:
            logging.error(str(e), 'Active profile open beelden links file path could not be made absolute. '
                          'Prepare for things to go wrong in unittests.')

