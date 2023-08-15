import re

from typing import List


def parse_role_label(role_label: str, separators: List[str]):
    """Parses the role label by splitting on a number of possible separators.
    Note that the resulting strings are not stripped of whitespace, as
    this is not necessary for later processing
    :param role_string the string containing one or more roles
    :param separators a list of the possible separators
    :returns a list of possible role strings"""
    # Note: the reason to put this in a function rather than using the regex
    # directly is to be able to test how well it works on the labels

    return re.split("|".join(separators), role_label)


def check_word_in_string(word: str, string: str):
    return f" {word} " in f" {string} "


def match_role(role_strings: List[str], possible_role_groups: List[List[str]]):
    """Matches the role strings with the possible roles
    :param role_strings - the role strings extracted from the label
    :param possible_roles - a list of the groups of roles, each group is a list of the roles
    that contain the same text (e.g. blokfluit, blokfluit alt, blokfluit bas)
    :returns a list of the matched roles"""

    matched_roles = []
    for possible_role_group in possible_role_groups:
        for role_string in role_strings:
            possible_matches_for_string = []
            for possible_role in possible_role_group:
                if (
                    check_word_in_string(possible_role, role_string)
                    and possible_role not in possible_matches_for_string
                ):
                    possible_matches_for_string.append(possible_role)
            # if multiple matches
            if len(possible_matches_for_string) > 1:
                lengths = [len(s) for s in possible_matches_for_string]
                longest_match = possible_matches_for_string[lengths.index(max(lengths))]
                matched_roles.append(longest_match)  # take the longest match

                # check if the other matches exist in addition to the longest
                string_without_longest = role_string.replace(longest_match, "")
                for other_possible_role in possible_matches_for_string:
                    if check_word_in_string(
                        other_possible_role, string_without_longest
                    ):
                        matched_roles.append(other_possible_role)
            else:
                matched_roles.extend(possible_matches_for_string)

    return list(set(matched_roles))  # remove duplicates
