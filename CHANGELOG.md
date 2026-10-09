# Changelog

## 1.0.0a4 (unreleased)


- Nothing changed yet.


## 1.0.0a3 (2026-10-10)

- Declare block-api 2.0 for the Plate 53 editor (upgrade step 1002). A 2.0
  host skips every 1.x declaration. The bundle needs no rebuild: it imports
  none of the `platejs` names 2.0 removed.


## 1.0.0a2 (2026-10-08)


- Nothing changed yet.


## 1.0.0a1 (2026-10-04)

- The editor needs nothing from a provider add-on any more. The fragment
  block's `install()` fetches the new `@fragments` service and registers
  every provider's fragments before the first render; the host awaits it
  (`plone.blicca.auroraeditor` 1.0.0a3, block-api 1.2, declared on the
  record by upgrade step 1001). A theme ships its `fragments/*.html` and
  the `fragments:folder` line, no editor bundle, no record, no rebuild.
  `IFragmentsProvider` gains `records()`; a fragment's title is its
  first-line `<!-- title: … -->` comment, else derived from the file name
  (ADR 0002).

- Add the `fragments:folder` ZCML directive. A provider add-on registers
  its fragments folder with one line in `configure.zcml` and no Python
  code. The folder is resolved relative to the package, checked at
  startup, and registered under the package name unless `name` is given.

- Register the `INonInstallable` utility that hides the uninstall profile.
  `HiddenProfiles` was defined in `setuphandlers.py` but never registered in
  `configure.zcml`, so it hid nothing: harmless while this package has no
  upgrade profile, and a profile offered as an installable add-on of its own
  the moment one is scaffolded.

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
