from enum import Enum, unique


@unique
class DatasetApiUriLevel(Enum):
    DATASET = "dataset"
    DATACATALOG = "datacatalog"
    DATADOWNLOAD = "datadownload"
