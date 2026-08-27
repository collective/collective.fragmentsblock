"""Resolve and render registered fragment markup (server side).

A fragment is a static HTML file — typically cut verbatim from a design
mockup — shipped by a provider add-on. The editor half registers id, title
and the same markup into ``@plone/registry`` (see ``bundle-src``); this
module is the classic-rendering counterpart: named ``IFragmentsProvider``
utilities map fragment ids to the raw HTML, and ``substitute`` mirrors the
JS ``renderFragmentHtml`` semantics 1:1 so both surfaces emit identical
markup — ``${var}`` tokens filled from the block's persisted ``variables``
mapping, missing variables as empty strings, every value HTML-escaped.

Everything is fail-soft: an unknown id, an unregistered provider or an
unreadable file degrades to ``None`` (the caller emits an invisible
placeholder), never a broken page.
"""

import html
import math
import re
from logging import getLogger
from pathlib import Path

from zope.component import getUtilitiesFor
from zope.interface import implementer

from collective.fragmentsblock.interfaces import IFragmentsProvider


logger = getLogger(__name__)

# Registration names are filesystem-safe slugs; anything else (e.g. a path
# traversal attempt through the block data) simply does not resolve.
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

_TOKEN_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


@implementer(IFragmentsProvider)
class FragmentsFolder:
    """The stock provider: one ``<fragment_id>.html`` file per fragment.

    Point it at the directory of verbatim mockup files inside the provider
    package — the same files whose ``?raw`` imports the provider's editor
    bundle registers — and register it as a named utility::

        <utility
            name="my.theme"
            provides="collective.fragmentsblock.interfaces.IFragmentsProvider"
            component="my.theme.fragments.provider"
            />
    """

    def __init__(self, directory):
        self.directory = Path(directory)

    def get(self, fragment_id):
        path = self.directory / f"{fragment_id}.html"
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None


def resolve(fragment_id):
    """The raw HTML registered for ``fragment_id``, or ``None``.

    Ids share one flat, site-wide namespace across every provider:
    providers are asked in utility-name order and the first hit wins, so a
    second provider reusing an id shadows the first (the editor-side
    registry, keyed by name, resolves such a clash the same way).
    """
    if not isinstance(fragment_id, str) or not _ID_RE.match(fragment_id):
        return None
    for _name, provider in sorted(getUtilitiesFor(IFragmentsProvider)):
        try:
            markup = provider.get(fragment_id)
        except Exception:
            logger.exception("Fragments provider %r failed for %r", _name, fragment_id)
            continue
        if markup is not None:
            return markup
    return None


def coerce(value):
    """The coercion table both halves implement (``fragments.ts coerce``).

    Values arrive as JSON, so booleans and numbers are ordinary; each one
    is rendered the way JavaScript renders it, because the editor cannot
    render it any other way and the two surfaces must agree. Anything
    outside the table (lists, dicts) renders empty rather than as a
    Python-flavoured string.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    # before int: bool is an int subclass
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        # JS has one number type: 1.0 prints as "1"
        return str(int(value)) if value.is_integer() else repr(value)
    return ""


def substitute(markup, variables):
    """Fill ``${var}`` tokens; mirrors the JS ``renderFragmentHtml``."""
    values = variables if isinstance(variables, dict) else {}

    def _value(match):
        name = match.group(1)
        if name not in values:
            return ""
        # quote=True gives exactly the JS escape set: & < > " ' -> &#x27;
        return html.escape(coerce(values[name]), quote=True)

    return _TOKEN_RE.sub(_value, markup)


def fragment_html(data):
    """The rendered markup of a fragment block dict, or ``None``."""
    markup = resolve((data or {}).get("fragment"))
    if markup is None:
        return None
    return substitute(markup, (data or {}).get("variables"))
