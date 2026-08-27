"""Unit tests for the server-side fragment resolution and substitution.

The ``substitute`` semantics are the contract shared with the JS
``renderFragmentHtml`` (bundle-src/src/fragments.ts): both sides must emit
identical markup from the same file and block data.
"""

from pathlib import Path

from collective.fragmentsblock.fragments import FragmentsFolder
from collective.fragmentsblock.fragments import resolve
from collective.fragmentsblock.fragments import substitute


FIXTURES = Path(__file__).parent / "fragments"


class TestFragmentsFolder:
    def test_reads_fragment_file(self):
        markup = FragmentsFolder(FIXTURES).get("contact-box")
        assert '<aside class="contact-box">' in markup

    def test_unknown_id_is_none(self):
        assert FragmentsFolder(FIXTURES).get("nope") is None


class TestResolve:
    def test_rejects_non_slug_ids_before_any_provider(self):
        # path traversal shapes never reach a provider's filesystem
        assert resolve("../secret") is None
        assert resolve("a/b") is None
        assert resolve(None) is None
        assert resolve("") is None


class TestSubstitute:
    def test_markup_without_tokens_is_verbatim(self):
        markup = '<div class="a">&amp; ok</div>'
        assert substitute(markup, None) == markup

    def test_tokens_filled_escaped_missing_empty(self):
        markup = "<p>${phone}</p><p>${missing}</p>"
        out = substitute(markup, {"phone": "<b>+49 & 30</b>", "extra": "x"})
        assert out == "<p>&lt;b&gt;+49 &amp; 30&lt;/b&gt;</p><p></p>"

    def test_none_value_is_empty(self):
        assert substitute("<p>${phone}</p>", {"phone": None}) == "<p></p>"

    def test_quotes_escaped_like_the_js_half(self):
        out = substitute("${v}", {"v": "\"a\" 'b' & <c>"})
        assert out == "&quot;a&quot; &#x27;b&#x27; &amp; &lt;c&gt;"


class TestCoerceParity:
    """The coercion table is the JS half's, value for value.

    Each expectation here is what ``String(value)`` produces in JavaScript
    (``bundle-src/src/fragments.ts``), not what ``str(value)`` produces in
    Python — the editor cannot render these any other way, and the two
    surfaces must emit the same markup. The mirror-image cases live in
    ``bundle-src/test/fragment-block.test.tsx``.
    """

    def test_booleans_render_lowercase(self):
        assert substitute("${v}", {"v": True}) == "true"
        assert substitute("${v}", {"v": False}) == "false"

    def test_integers_render_as_decimals(self):
        assert substitute("${v}", {"v": 0}) == "0"
        assert substitute("${v}", {"v": -42}) == "-42"

    def test_integral_floats_lose_the_decimal_point(self):
        assert substitute("${v}", {"v": 1.0}) == "1"
        assert substitute("${v}", {"v": 2.5}) == "2.5"

    def test_containers_render_empty(self):
        assert substitute("${v}", {"v": ["a", "b"]}) == ""
        assert substitute("${v}", {"v": {"k": 1}}) == ""

    def test_prototype_shaped_names_are_not_special(self):
        # ${toString} resolves to nothing here and, since the JS half uses
        # Object.hasOwn, to nothing there either
        assert substitute("${toString}${constructor}", {}) == ""
        assert substitute("${toString}", {"toString": "x"}) == "x"
