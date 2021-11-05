import json
import pytest
from util import OpenBeeldenLinkRetriever as ob


@pytest.mark.parametrize(('ob_source', 'hasFormat', 'identifier'), [
    ('DERDE', 'test.mp4', 'PGM4011338'),
    ('WEEKNUMMER373-HRE0001555F', 'test.mp4', '518948'),
    ("", "https://www.openbeelden.nl/files/11/52/1156335.1152492.WEEKNUMMER482_HRE0000DEF4_261000_424000.m3u8", "")
])
def test_create_candidate_queries(ob_source, hasFormat, identifier):
    DUMMY_INPUT = {"_source": {"@graph": {}}}
    if hasFormat:
        DUMMY_INPUT["_source"]["@graph"]["dcterms:hasFormat"] = [hasFormat]

    if identifier:
        DUMMY_INPUT["_source"]["@graph"]["dcterms:identifier"] = identifier

    candidate_queries = ob.generate_candidate_queries(ob_source, DUMMY_INPUT)

    print(json.dumps(candidate_queries))
