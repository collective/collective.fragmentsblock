"""The blocks view links the stylesheet outside Plone's resource registry, so
it ships minified."""

import re
from pathlib import Path


STYLESHEET = Path(__file__).parent.parent / "static" / "fragment-block.css"
STALE = "fragment-block.css is not minified: run `pnpm build` in bundle-src/"


class TestStylesheet:
    def test_ships_without_comments(self):
        assert "/*" not in STYLESHEET.read_text(), STALE

    def test_ships_without_indentation(self):
        assert not re.search(r"^\s", STYLESHEET.read_text(), re.MULTILINE), STALE
