import pytest

from models.DAANRdfModel import CLASS_URIS_FOR_DAAN_LEVELS, NON_GTAA_TYPES


@pytest.mark.parametrize(
    "non_gtaa_type",
    [
        "http://data.rdlabs.beeldengeluid.nl/schema/Broadcaster",
        "http://data.rdlabs.beeldengeluid.nl/schema/BroadcastStation",
        "http://data.rdlabs.beeldengeluid.nl/schema/Language",
        "http://data.rdlabs.beeldengeluid.nl/schema/TargetGroup",
    ],
)
def test_non_gtaa_type(non_gtaa_type):
    assert non_gtaa_type in NON_GTAA_TYPES


@pytest.mark.parametrize(
    "daan_level",
    [
        "SERIES",
        "SEASON",
        "PROGRAM",
        "LOGTRACKITEM",
        "ITEM",
        # "AGGREGATEASSET", # should be added?
    ],
)
def test_get_class_uri_for_valid_daan_level(daan_level):
    CLASS_URIS_FOR_DAAN_LEVELS[daan_level]


@pytest.mark.parametrize(
    "daan_level",
    [
        "nonsense",
        "series",
    ],
)
def test_get_class_uri_for_invalid_daan_level(daan_level):
    with pytest.raises(KeyError):
        CLASS_URIS_FOR_DAAN_LEVELS[daan_level]
