import pytest

from models.SDORdfModel import CLASS_URIS_FOR_DAAN_LEVELS


@pytest.mark.parametrize(
    "daan_level",
    [
        "SERIES",
        "SEASON",
        "PROGRAM",
        "LOGTRACKITEM",
        "ITEM",
        # "AGGREGATEASSET", # should allso have a uri?
    ],
)
def test_class_uri_for_valid_daan_levels_init(daan_level):
    CLASS_URIS_FOR_DAAN_LEVELS[daan_level]


@pytest.mark.parametrize(
    "daan_level",
    [
        "nonsense",
        "Series",  # incorrect capitalization
    ],
)
def test_class_uri_for_invalid_daan_levels_init(daan_level):
    with pytest.raises(KeyError):
        CLASS_URIS_FOR_DAAN_LEVELS[daan_level]
