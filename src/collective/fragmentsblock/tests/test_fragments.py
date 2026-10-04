"""Unit tests for the server-side fragment resolution and substitution.

The ``substitute`` semantics are the contract shared with the JS
``renderFragmentHtml`` (bundle-src/src/fragments.ts): both sides must emit
identical markup from the same file and block data.
"""

from pathlib import Path
from unittest.mock import patch

from collective.fragmentsblock.fragments import derived_title
from collective.fragmentsblock.fragments import FragmentsFolder
from collective.fragmentsblock.fragments import records
from collective.fragmentsblock.fragments import resolve
from collective.fragmentsblock.fragments import substitute
from collective.fragmentsblock.fragments import title_of


FIXTURES = Path(__file__).parent / "fragments"


class TestFragmentsFolder:
    def test_reads_fragment_file(self):
        markup = FragmentsFolder(FIXTURES).get("contact-box")
        assert '<aside class="contact-box">' in markup

    def test_unknown_id_is_none(self):
        assert FragmentsFolder(FIXTURES).get("nope") is None

    def test_lists_every_file_whose_name_is_an_id(self):
        found = FragmentsFolder(FIXTURES).records()
        assert [record["id"] for record in found] == ["contact-box", "seal"]
        # "not an id.html" is in the folder and never a record

    def test_records_carry_the_file_verbatim(self):
        (contact_box, _seal) = FragmentsFolder(FIXTURES).records()
        assert contact_box["html"] == (FIXTURES / "contact-box.html").read_text(encoding="utf-8")

    def test_records_are_titled(self):
        (contact_box, seal) = FragmentsFolder(FIXTURES).records()
        assert contact_box["title"] == "Contact box"  # derived from the file name
        assert seal["title"] == "Seal of approval"  # the comment header

    def test_missing_folder_lists_nothing(self):
        assert FragmentsFolder(FIXTURES / "nope").records() == []


class TestTitles:
    def test_header_comment_wins(self):
        assert title_of("x", "<!-- title: Contact box -->\n<aside/>") == "Contact box"

    def test_header_may_be_indented_and_padded(self):
        markup = "\n  <!--  title:   Partner logos  (strip)\n  -->\n<div/>"
        assert title_of("x", markup) == "Partner logos (strip)"

    def test_only_the_first_thing_in_the_file_counts(self):
        assert title_of("contact-box", "<div/>\n<!-- title: Late -->") == "Contact box"

    def test_other_comments_are_not_titles(self):
        assert title_of("contact-box", "<!-- TODO: spacing -->\n<div/>") == "Contact box"

    def test_empty_header_falls_back(self):
        assert title_of("contact-box", "<!-- title: -->\n<div/>") == "Contact box"

    def test_derived_from_the_id(self):
        assert derived_title("contact-box") == "Contact box"
        assert derived_title("partner_logos") == "Partner logos"
        assert derived_title("CTA-Banner") == "CTA Banner"
        assert derived_title("seal") == "Seal"


class StubProvider:
    def __init__(self, found):
        self.found = found

    def get(self, fragment_id):
        return None

    def records(self):
        if isinstance(self.found, Exception):
            raise self.found
        return self.found


def providers(*named):
    return patch("collective.fragmentsblock.fragments.getUtilitiesFor", return_value=list(named))


class TestRecords:
    """Enumeration across providers, in ``resolve`` order."""

    def test_first_provider_wins_a_clashing_id(self):
        first = StubProvider([{"id": "seal", "title": "First", "html": "<b/>"}])
        second = StubProvider([
            {"id": "seal", "title": "Second", "html": "<i/>"},
            {"id": "banner", "title": "Banner", "html": "<u/>"},
        ])
        with providers(("b.second", second), ("a.first", first)):
            found = records()
        assert [(r["id"], r["title"]) for r in found] == [("seal", "First"), ("banner", "Banner")]

    def test_a_failing_provider_is_skipped(self):
        broken = StubProvider(RuntimeError("disk gone"))
        with providers(("a.broken", broken), ("b.folder", FragmentsFolder(FIXTURES))):
            found = records()
        assert [r["id"] for r in found] == ["contact-box", "seal"]

    def test_malformed_records_are_dropped(self):
        sloppy = StubProvider([
            {"id": "../etc", "title": "Traversal", "html": "<b/>"},
            {"id": "no-html", "title": "No markup"},
            {"id": "untitled", "html": "<b/>"},
            "not even a dict",
        ])
        with providers(("a", sloppy)):
            found = records()
        assert found == [{"id": "untitled", "title": "Untitled", "html": "<b/>"}]

    def test_no_providers(self):
        with providers():
            assert records() == []


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
