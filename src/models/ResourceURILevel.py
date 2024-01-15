from enum import Enum, unique

@unique
class ResourceURILevel(Enum):
    PROGRAM = "program"
    SERIES = "series"
    SEASON = "season"
    SCENE = "scene"
    DATASET = "dataset"
    DATACATALOG = "datacatalog"
    DATADOWNLOAD = "datadownload"