# Changelog

## 1.0.0a1 (unreleased)

- A fragment block now **names itself with the fragment's title** while blocks
  are dragged. The editor collapses the canvas to one row per block and reads
  each row's identifying line off the rendered block — but a fragment is a
  piece of a design and is often pure decoration with no text at all, so every
  fragment row read "Fragment" against an empty line and two of them in one
  page were indistinguishable exactly while being reordered. The view stamps
  `data-block-summary` with the record's title (block add-on contract §1.6),
  which is the same string the picker offers, so the row reads "Fragment —
  Balkenlage (Trenner)". Editing affordance only: the attribute is inert on
  the classic page, whose server-rendered markup does not carry it.

- The fragment block's settings form now carries **block width** and
  **background** — the two placement controls, offered because a fragment
  is a piece of a design rather than a whole one: a contact box wants the
  narrow column, a divider the full bleed, and the same file may want both
  on two different pages. Both are Aurora style fields, so the editor and
  the classic renderer stamp the class and custom properties on the block
  wrapper generically — no change to either view component or to
  `@@aurora-block-fragment`. Width defaults to `default`, the width
  fragment blocks already rendered at, so existing content is unchanged;
  the background slots are read from the host's registered palette and the
  field is omitted on a host that registers none.

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
