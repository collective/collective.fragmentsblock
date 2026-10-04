"""Resolve, enumerate and render registered fragment markup (server side).

A fragment is a static HTML file — typically cut verbatim from a design
mockup — shipped by a provider add-on. Named ``IFragmentsProvider``
utilities map fragment ids to the raw HTML. Classic rendering resolves one
id at a time; the editor fetches ``records()`` through the ``@fragments``
service when it opens and registers each record into ``@plone/registry``
(ADR 0002), so both surfaces read the same files. ``substitute`` mirrors the
JS ``renderFragmentHtml`` semantics 1:1 so both emit identical markup —
``${var}`` tokens filled from the block's persisted ``variables`` mapping,
missing variables as empty strings, every value HTML-escaped.

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

# The optional title line: the first thing in the file, before any markup.
_TITLE_RE = re.compile(r"\A\s*<!--\s*title:\s*(.*?)\s*-->", re.DOTALL)


def derived_title(fragment_id):
    """``contact-box`` -> ``Contact box``; the title when the file has none."""
    words = " ".join(part for part in re.split(r"[-_]+", fragment_id) if part)
    return words[:1].upper() + words[1:]


def title_of(fragment_id, markup):
    """The picker title: the ``<!-- title: ... -->`` header, else derived."""
    match = _TITLE_RE.match(markup)
    if match and match.group(1):
        return " ".join(match.group(1).split())
    return derived_title(fragment_id)


@implementer(IFragmentsProvider)
class FragmentsFolder:
    """The stock provider: one ``<fragment_id>.html`` file per fragment.

    Registered by the ``fragments:folder`` ZCML directive (``zcml.py``).
    """

    def __init__(self, directory):
        self.directory = Path(directory)

    def get(self, fragment_id):
        path = self.directory / f"{fragment_id}.html"
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None

    def records(self):
        found = []
        for path in sorted(self.directory.glob("*.html")):
            if not _ID_RE.match(path.stem):
                logger.warning(
                    "Fragments folder %s: skipping %s, its name is not a fragment id",
                    self.directory,
                    path.name,
                )
                continue
            try:
                markup = path.read_text(encoding="utf-8")
            except OSError:
                logger.exception("Fragments folder %s: cannot read %s", self.directory, path.name)
                continue
            found.append({"id": path.stem, "title": title_of(path.stem, markup), "html": markup})
        return found


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


def records():
    """Every fragment of every provider, as the ``@fragments`` service lists them.

    Providers are asked in the order ``resolve`` consults them and the first
    record of an id wins, so the editor's picker and the classic renderer
    agree about which provider owns a clashing id. A record a provider got
    wrong (no slug id, no string markup) is dropped with a warning rather
    than handed to the editor, which could not render it.
    """
    seen = set()
    found = []
    for _name, provider in sorted(getUtilitiesFor(IFragmentsProvider)):
        try:
            provided = list(provider.records())
        except Exception:
            logger.exception("Fragments provider %r failed to list its fragments", _name)
            continue
        for record in provided:
            fragment_id = record.get("id") if isinstance(record, dict) else None
            if (
                not isinstance(fragment_id, str)
                or not _ID_RE.match(fragment_id)
                or not isinstance(record.get("html"), str)
            ):
                logger.warning(
                    "Fragments provider %r: dropping a malformed record %r", _name, record
                )
                continue
            if fragment_id in seen:
                continue
            seen.add(fragment_id)
            found.append({
                "id": fragment_id,
                "title": record.get("title") or derived_title(fragment_id),
                "html": record["html"],
            })
    return found


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
