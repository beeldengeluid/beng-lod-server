import pytest

from models.DAANJsonModel import LogTrackType, ObjectType


@pytest.mark.parametrize(
    "logtrack_type",
    [
        "Actions",
        "Agenda Point",
        "Baton errors (compliance/auto)",
        "Baton remarks (compliance|auto)",
        "Composition",
        "Extracted Data",
        "Extracted Labels",
        "Face Labels",
        "Markus testing GMI logtracks",
        "My Scenes",
        "ProgramSiteID",
        "Scene Desc Logtrack",
        "Scene description",
        "scenedesc",
        "Scenedesc",
        "Speaker Labels",
        "Story",
        "Studio Player Log Entry",
        "Subtitles (Cavena 890)",
        "Subtitles",
        "Technical Logtrack",
        "technical",
        "Technical",
        "Transcripted Speech",
        # "Baton remarks (compliance/auto)"  # this one is not valid?
    ],
)
def test_logtrack_type_init_valid(logtrack_type):
    logtrack_type = LogTrackType(logtrack_type)
    assert isinstance(logtrack_type, LogTrackType)


@pytest.mark.parametrize(
    "logtrack_type",
    [
        "nonsense",
        "SceneDesc",  # incorrect capitalization
    ],
)
def test_logtrack_type_init_invalid(logtrack_type):
    with pytest.raises(ValueError):
        LogTrackType(logtrack_type)


@pytest.mark.parametrize(
    "object_type",
    [
        "SERIES",
        "SEASON",
        "PROGRAM",
        "LOGTRACKITEM",
        "ITEM",
        "AGGREGATEASSET",
    ],
)
def test_object_type_init_valid(object_type):
    object_type = ObjectType(object_type)
    assert isinstance(object_type, ObjectType)


@pytest.mark.parametrize(
    "object_type",
    [
        "nonsense",
        "series",  # incorrect capitalization
    ],
)
def test_object_type_init_invalid(object_type):
    with pytest.raises(ValueError):
        ObjectType(object_type)
