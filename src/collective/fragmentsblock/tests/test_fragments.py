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
