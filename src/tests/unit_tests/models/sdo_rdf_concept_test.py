import pytest

from mockito import when

from models.SDORdfConcept import SDORdfConcept


@pytest.fixture(scope="function")
def sdo_rdf_concept(i_dmapi_program, sdo_rdf_profile):
    metadata = i_dmapi_program["_source"]
    content_type = "PROGRAM"
    cache = {}
    yield SDORdfConcept(metadata, content_type, sdo_rdf_profile, cache)


@pytest.mark.parametrize(
    ("used_path, concept_name, expected_result"),
    [
        ("test_path", "dummy concept name", None),  # no comma in path
        ("test_path, test_path2", "dummy concept name", None),  # path too short
        (
            "test_concept2, test.something_else, resolved_value",
            "dummy concept name",
            None,
        ),
        # metadata does not contain the name field
        ("test_concept3, test.name, resolved_value", "dummy concept name", None),
        # metadata does not contain the role field
        ("test_concept4, test.name, resolved_value", "dummy concept name", None),
        # metadata does not contain the resolved_value field
        (
            "test_concept5, test.name, extra_level, resolved_value",
            "dummy concept name",
            None,
        ),
        # metadata doesn't contain the resolved_value
        ("test_concept, test.name, resolved_value", "some other concept name", None),
        # concept name doesn't match
        ("test_concept, test.name, resolved_value", "dummy concept name", "role name"),
        # concept should return correctly
    ],
)
def test_get_role(used_path, concept_name, expected_result):
    payload = {
        "test_concept": {
            "test.name": {"resolved_value": "dummy concept name"},
            "test.role": {"resolved_value": "role name"},
        },
        "test_concept2": {
            "test.something_else": {"resolved_value": "dummy concept name"},
            "test.role": {"resolved_value": "role name"},
        },
        "test_concept3": {
            "test.name": {"resolved_value": "dummy concept name"},
            "test.something_else": {"resolved_value": "role name"},
        },
        "test_concept4": {
            "test.name": {"resolved_value": "dummy concept name"},
            "test.role": {"something_else": "role name"},
        },
        "test_concept5": {
            "test.name": {
                "extra_level": {"resolved_value": "dummy concept name"},
            },
            "test.role": {"something_else": "role name"},
        },
    }

    assert SDORdfConcept._get_role(used_path, payload, concept_name) == expected_result


def test_init(sdo_rdf_concept):
    assert isinstance(sdo_rdf_concept, SDORdfConcept)


def test_create_role_groups():
    role_data = {
        "cello": {"dummy": "test"},
        "cellocaster": {"dummy": "test"},
        "hobo": {"dummy": "test"},
        "Alt Cello": {"dummy": "test"},
        "alt-cello": {"dummy": "test"},
        "hellocellobello": {"dummy": "test"},
        "piano": {"dummy": "test"},
        "tekst": {"dummy": "test"},
    }

    groups = SDORdfConcept.create_role_groups(role_data)

    assert ["hobo"] in groups
    assert ["piano"] in groups
    assert [
        "cello",
        "cellocaster",
        "Alt Cello",
        "alt-cello",
        "hellocellobello",
    ] in groups

    # check the group members are not in as individual groups
    for group_member in [
        "cello",
        "cellocaster",
        "Alt Cello",
        "alt-cello",
        "hellocellobello",
    ]:
        assert [group_member] not in groups


@pytest.mark.parametrize(
    ("role_string", "expected_result"),
    [
        ("", []),
        ("something", []),
        ("dummy", [("um-id-1", "um 1")]),
        ("another dummy", [("wd-id-3", "WD 3"), ("um-id-3", "um 3")]),
        ("test", [("wd-id-1", "WD 1")]),
        ("test test", [("wd-id-1", "WD 1")]),
        ("trial", [("wd-id-2", "WD 2"), ("um-id-2", "um 2")]),
        (
            "dummy, trial",
            [("um-id-1", "um 1"), ("wd-id-2", "WD 2"), ("um-id-2", "um 2")],
        ),
        ("trial/test", [("wd-id-1", "WD 1"), ("wd-id-2", "WD 2"), ("um-id-2", "um 2")]),
        (
            "dummy and another dummy",
            [("wd-id-3", "WD 3"), ("um-id-3", "um 3"), ("um-id-1", "um 1")],
        ),
    ],
)
def test_get_role_uris_and_labels(role_string, expected_result, sdo_rdf_concept):
    dummy_mapping = {
        "dummy": {
            "wikidata_identifier": "",
            "wikidata_label": "",
            "um_identifier": "um-id-1",
            "um_label": "um 1",
        },
        "test": {
            "wikidata_identifier": "wd-id-1",
            "wikidata_label": "WD 1",
            "um_identifier": "",
            "um_label": "",
        },
        "trial": {
            "wikidata_identifier": "wd-id-2",
            "wikidata_label": "WD 2",
            "um_identifier": "um-id-2",
            "um_label": "um 2",
        },
        "another dummy": {
            "wikidata_identifier": "wd-id-3",
            "wikidata_label": "WD 3",
            "um_identifier": "um-id-3",
            "um_label": "um 3",
        },
    }

    dummy_groups = [["dummy", "another dummy"], ["test"], ["trial"]]

    with when(sdo_rdf_concept).get_role_data().thenReturn(
        {"groups": dummy_groups, "mapping": dummy_mapping}
    ):
        result_uris_and_labels = sdo_rdf_concept.get_role_uris_and_labels(role_string)
        for result_uri_and_label in result_uris_and_labels:
            assert result_uri_and_label in expected_result
        for result_uri_and_label in expected_result:
            assert result_uri_and_label in result_uris_and_labels
