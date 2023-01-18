import pytest

from models.SDORdfConcept import SDORdfConcept


@pytest.fixture(scope="function")
def sdo_rdf_concept(i_dmapi_program, sdo_rdf_profile):
    metadata = i_dmapi_program["_source"]
    content_type = "PROGRAM"
    cache = {}
    yield SDORdfConcept(metadata, content_type, sdo_rdf_profile, cache)


def test_init(sdo_rdf_concept):
    assert isinstance(sdo_rdf_concept, SDORdfConcept)
