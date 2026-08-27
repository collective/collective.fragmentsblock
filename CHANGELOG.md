# Changelog

## 1.0.0a1 (unreleased)

- Initial release: the Aurora **fragment block** (`@type: fragment`) —
  drop registered **design fragments** (static HTML files, typically cut
  verbatim from a design mockup) into any Aurora-edited page. Aurora-first:
  provider add-ons register `{id, title, html}` records into the shared
  `@plone/registry` singleton from their install function
  (`type: collective.fragmentsblock.fragment`); the block enumerates them
  for its picker and renders the markup client-side, as-is, with optional
  `${var}` substitution from the block's persisted `variables` mapping
  (HTML-escaped, missing variables empty). Blicca classic pages render the
  same file server-side via `@@aurora-block-fragment` and named
  `IFragmentsProvider` utilities (`FragmentsFolder` reads
  `<id>.html` files from a provider package directory) with identical
  substitution semantics. Fail-soft placeholders everywhere; ships both
  halves of the Blicca block add-on contract, with the committed editor
  bundle built from `bundle-src/`
  (`@plone-collective/aurora-fragment-block`). Variables render on both
  surfaces but have no sidebar UI yet — see
  `docs/adr/0001-fragments-are-registered-static-markup.md` for the design
  and its deferred parts.
