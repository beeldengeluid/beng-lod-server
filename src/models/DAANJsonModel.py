from enum import Enum, unique  # https://docs.python.org/3.5/library/enum.html

"""Contains models for the DAAN data"""

""" -------------- ENUMS FOR STRONG TYPING --------------- """


@unique
class ObjectType(Enum):  # models object/record types in DAAN
    SERIES = "SERIES"
    SEASON = "SEASON"
    PROGRAM = "PROGRAM"
    ITEM = "ITEM"
    AGGREGATEASSET = "AGGREGATEASSET"
    LOGTRACKITEM = "LOGTRACKITEM"


@unique
class LogTrackType(Enum):  # models the logtrack types in DAAN
    # as described in the documentation
    SCENE_DESC = "scenedesc"
    TECHNICAL = "Technical"
    SUBTITLES = "Subtitles"
    FACE_LABELS = "Face Labels"
    BATON_REMARKS = "Baton remarks (compliance/auto)"  # this one is not valid?
    SPEAKER_LABELS = "Speaker Labels"
    ACTIONS = "Actions"
    EXTRACTED_LABELS = "Extracted Labels"
    SPEECH_TRANSCRIPT = "Transcripted Speech"

    # found after importing
    AGENDA_POINT = "Agenda Point"
    BATON_ERRORS = "Baton errors (compliance/auto)"
    BATON_REMARKS2 = "Baton remarks (compliance|auto)"
    SUBTITLES_C890 = "Subtitles (Cavena 890)"
    STORY = "Story"
    COMPOSITION = "Composition"
    EXTRACTED_DATA = "Extracted Data"
    SCENE_DESC2 = "Scenedesc"
    SCENE_DESC3 = "Scene description"
    SCENE_DESC4 = "Scene Desc Logtrack"
    MY_SCENES = "My Scenes"
    MARKUS = "Markus testing GMI logtracks"
    PROGRAMSITEID = "ProgramSiteID"
    STUDIO_PLAYER = "Studio Player Log Entry"
    TECHNICAL2 = "Technical Logtrack"
    TECHNICAL3 = "technical"

    # fall back type
    UNKNOWN = "unknown"


# some important DAAN field names
DAAN_PARENT = "parents"
DAAN_PARENT_ID = "parent_id"
DAAN_PARENT_TYPE = "parent_type"
DAAN_PROGRAM_ID = "program_ref_id"
DAAN_PAYLOAD = "payload"
DAAN_TYPE = "viz_type"


def isSceneDescription(logtrack_type):
    """Checks if the logtrack type indicates it is a Scene Description"""
    return (
        logtrack_type == LogTrackType.SCENE_DESC.value
        or logtrack_type == LogTrackType.SCENE_DESC2.value
        or logtrack_type == LogTrackType.SCENE_DESC3.value
        or logtrack_type == LogTrackType.SCENE_DESC4.value
    )
