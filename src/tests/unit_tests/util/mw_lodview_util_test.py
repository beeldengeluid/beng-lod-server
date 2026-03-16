import pytest
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDFS, SKOS, SDO, DCTERMS  # type: ignore
import util.mw_lodview_util


@pytest.mark.parametrize(
    "iri,expected",
    [
        (
            "http://example.org/property",
            {
                "uri": "http://example.org/property",
                "prefix": "ex",
                "namespace": "http://example.org/",
                "property": "property",
            },
        ),
        (
            "http://example.org/",
            {
                "uri": "http://example.org/",
                "prefix": "",
                "namespace": "",
                "property": "",
            },
        ),
    ],
)
def test_json_parts_from_IRI(iri: str, expected: dict):
    """Deconstruct the given IRI into its parts and return them in a dict.
    The parts are prefix, namespace and property."""
    DUMMY_GRAPH = Graph()
    DUMMY_GRAPH.bind("ex", "http://example.org/")
    result = util.mw_lodview_util.json_parts_from_IRI(DUMMY_GRAPH, iri)
    assert result == expected


@pytest.mark.parametrize(
    "label_type", [RDFS.label, SKOS.prefLabel, SDO.name, DCTERMS.title]
)
@pytest.mark.parametrize("lang", ["", "nl", "en"])
def test_json_label_for_node(label_type: URIRef, lang: str):
    """Generates a list of all possible labels for a given IRI or BNode.
    This list is used for the visualisation of the resource in the LOD view.
    :param lang: the language preference for the labels.
    """
    DUMMY_URI = URIRef("http://example.org/01")
    DUMMY_LITERAL = Literal("test", lang="nl")
    test_graph = Graph(bind_namespaces="core")
    test_graph.add((DUMMY_URI, label_type, DUMMY_LITERAL))
    result = util.mw_lodview_util.json_label_for_node(test_graph, DUMMY_URI, lang)
    assert isinstance(result, list), "Apparently the wrong type is returned."
    for res in result:
        assert isinstance(res, str), "Apparently the wrong type is returned."
    if lang == "nl":
        assert result == ["test"], "Apparently the wrong label is returned."
    elif lang == "en":
        assert result == ["test @nl"], "Apparently the wrong label is returned."
    elif lang == "":
        assert result == ["test @nl"], "Apparently the wrong label is returned."
    else:
        assert result == ["test @nl"], "Apparently the wrong label is returned."


@pytest.mark.parametrize(
    "literal,lang,expected",
    [
        (Literal("test", lang="nl"), "nl", "test"),
        (Literal("test", lang="nl"), "en", "test @nl"),
        (Literal("test", lang="nl"), "", "test @nl"),
        (Literal("test"), "nl", "test"),
        (Literal("test"), "en", "test"),
        (Literal("test"), "", "test"),
    ],
)
def test_get_string_for_langstring(literal: Literal, lang: str, expected: str):
    """Tests the get_string_for_langstring function. Given a literal with or without
     a language tag, the function should return the string value of a literal, taking
    into account the language.
    """
    result = util.mw_lodview_util.get_string_for_langstring(literal, lang)
    assert result == expected
