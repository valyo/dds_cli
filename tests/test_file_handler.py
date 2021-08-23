# IMPORTS ################################################################################ IMPORTS #

# Standard library
import pathlib

# Installed
import pytest

# Own modules
from dds_cli import exceptions
from dds_cli import file_handler

# GLOBAL VARIABLES ############################################################## GLOBAL VARIABLES #

CONFIG_PATH = pathlib.Path("./tests/config")

# TESTS #################################################################################### TESTS #
# extract_config


def test_filehandler_extract_config_nosuchfile():
    """Non existent file should return configfilenotfounderror"""

    configfile = CONFIG_PATH / pathlib.Path("nosuchconfigfile.json")
    with pytest.raises(exceptions.ConfigFileNotFoundError):
        _ = file_handler.FileHandler.extract_config(configfile=configfile)


def test_filehandler_extract_config_empty():
    """Empty config should raise exception"""

    configfile = CONFIG_PATH / pathlib.Path("empty_config.json")
    with pytest.raises(exceptions.ConfigFileExtractionError):
        _ = file_handler.FileHandler.extract_config(configfile=configfile)


def test_filehandler_extract_config_no_fields():
    """Config file with no fields in should work"""

    configfile = CONFIG_PATH / pathlib.Path("no_fields_config.json")
    _ = file_handler.FileHandler.extract_config(configfile=configfile)


def test_filehandler_extract_config_with_fields():
    """Config file with fields should return the contents"""

    configfile = CONFIG_PATH / pathlib.Path("with_fields_config.json")
    config_contents = file_handler.FileHandler.extract_config(configfile=configfile)
    assert config_contents == {
        "username": "test_username",
        "password": "test_password",
        "project": "test_project",
    }


# def test_filehandler_config_empty():
#     """Empty config should result in extractionerror"""

#     configfile = CONFIG_PATH / pathlib.Path("empty_config.json")
#     _ = file_handler.FileHandler.extract_config(configfile=configfile)


# def test_ddsbaseclass_method_ls_config_no_fields():
#     """No contents ({} in file) config should result in extractionerror"""

#     with pytest.raises(exceptions.MissingCredentialsException) as miserr:
#         _ = base.DDSBaseClass(
#             method="ls", config=CONFIG_PATH / pathlib.Path("no_fields_config.json")
#         )

#     assert "options are missing" in str(miserr.value)


# def test_ddsbaseclass_method_ls_config_username(monkeypatch):
#     """Only username in config file"""

# with pytest.raises(exceptions.)
