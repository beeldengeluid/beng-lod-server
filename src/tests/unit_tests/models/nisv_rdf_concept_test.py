import pytest

from models.NISVRdfConcept import NISVRdfConcept


@pytest.fixture(scope="function")
def nisv_rdf_concept(i_dmapi_program, nisv_rdf_profile):
    metadata = i_dmapi_program["_source"]
    content_type = "PROGRAM"
    cache = {}
    yield NISVRdfConcept(metadata, content_type, nisv_rdf_profile, cache)


def test_init(nisv_rdf_concept):
    assert isinstance(nisv_rdf_concept, NISVRdfConcept)
