from enum import Enum, unique


@unique
class ResourceApiUriLevel(Enum):
    PROGRAM = "program"
    SERIES = "series"
    SEASON = "season"
    SCENE = "scene"
