import pytest

from models.SDORdfConcept import SDORdfConcept


@pytest.mark.parametrize(
    "used_path, expected_result",
    [
        ("test_path", None),  # no comma in path
        ("test_path, test_path2", None),  # path too short
        ("test_concept2, test.something_else, resolved_value", None),
        # metadata does not contain the name field
        ("test_concept3, test.name, resolved_value", None),
        # metadata does not contain the role field
        ("test_concept4, test.name, resolved_value", None),
        # metadata does not contain the resolved_value field
        ("test_concept5, test.name, extra_level, resolved_value", None),
        # metadata doesn't contain the resolved_value
        ("test_concept, test.name, resolved_value", "role name"),
        # concept should return correctly
    ],
)
def test_get_role(used_path, expected_result):
    payload = {
        "test_concept": {
            "test.name": {"resolved_value": "concept name"},
            "test.role": {"resolved_value": "role name"},
        },
        "test_concept2": {
            "test.something_else": {"resolved_value": "concept name"},
            "test.role": {"resolved_value": "role name"},
        },
        "test_concept3": {
            "test.name": {"resolved_value": "concept name"},
            "test.something_else": {"resolved_value": "role name"},
        },
        "test_concept4": {
            "test.name": {"resolved_value": "concept name"},
            "test.role": {"something_else": "role name"},
        },
        "test_concept5": {
            "test.name": {
                "extra_level": {"resolved_value": "concept name"},
            },
            "test.role": {"something_else": "role name"},
        },
    }

    assert SDORdfConcept._get_role(used_path, payload) == expected_result
