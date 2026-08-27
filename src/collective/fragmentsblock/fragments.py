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

    Providers are asked in utility-name order; ids are expected to be
    site-unique, so the first hit wins deterministically either way.
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


def substitute(markup, variables):
    """Fill ``${var}`` tokens; mirrors the JS ``renderFragmentHtml``."""
    values = variables if isinstance(variables, dict) else {}

    def _value(match):
        value = values.get(match.group(1))
        return "" if value is None else html.escape(str(value))

    return _TOKEN_RE.sub(_value, markup)


def fragment_html(data):
    """The rendered markup of a fragment block dict, or ``None``."""
    markup = resolve((data or {}).get("fragment"))
    if markup is None:
        return None
    return substitute(markup, (data or {}).get("variables"))
