import pytest

from util import role_util


@pytest.mark.parametrize(
    ("label", "expected_result"),
    [
        ("muziekregie", ["muziekregie"]),
        ("tekstbewerker/vertaler", ["tekstbewerker", "vertaler"]),
        ("zang / gitaar", ["zang ", " gitaar"]),
        ("zang bas-bariton", ["zang bas-bariton"]),
        ("citheron/un satyre ,  bariton", ["citheron", "un satyre ", "  bariton"]),
        ("harp + elektronica", ["harp ", " elektronica"]),
    ],
)
def test_parse_role_label(label, expected_result):
    result = role_util.parse_role_label(label, ["/", ",", "\+"])

    assert result == expected_result


@pytest.mark.parametrize(
    ("text", "test_string", "expected_result"),
    [
        ("alt", "alt wie ein baum", True),
        ("alt", "so alt wie ein baum", True),
        ("alt", "so alt", True),
        ("alt", "de alterst", False),
        ("alt", "de alterste man", False),
        ("alt", "alterste man", False),
    ],
)
def test_check_word_in_string(text, test_string, expected_result):
    assert role_util.check_word_in_string(text, test_string) == expected_result


@pytest.mark.parametrize(
    ("label_strings", "expected_matches"),
    [
        (["zang "], ["zang"]),
        (["zang alt hobo"], ["alt hobo", "zang"]),
        (["zang zang alt hobo"], ["alt hobo", "zang"]),
        (["zang alt hobo hobo"], ["alt hobo", "hobo", "zang"]),
        (["zang blokfluit"], ["zang", "blokfluit"]),
        (["zang blokfluit alt"], ["zang", "blokfluit alt"]),
        (["zang blokfluit alt blokfluit"], ["blokfluit", "blokfluit alt", "zang"]),
        (["zang", "blokfluit"], ["zang", "blokfluit"]),
        (["tekstbewerker", "vertaler"], ["tekstbewerker", "vertaler"]),
        (["basalt"], []),
    ],
)
def test_match_roles(label_strings, expected_matches):
    possible_roles = [
        ["zang"],
        ["alt", "alt hobo", "blokfluit alt"],
        ["hobo", "alt hobo"],
        ["gespr.tekst"],
        ["blokfluit", "blokfluit alt", "blokfluit soprano"],
        ["bewerker", "tekstbewerker"],
        ["tekst", "tekstbewerker"],
        ["vertaler"],
    ]
    result = role_util.match_role(label_strings, possible_roles)

    for match in result:
        assert match in expected_matches
    for match in expected_matches:
        assert result.count(match) == 1
