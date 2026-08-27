# collective.fragmentsblock

An **Aurora block add-on** for [Plone](https://plone.org): the **fragment
block** (`@type: fragment`) drops registered **design fragments** — static
pieces of markup, typically cut verbatim from a design mockup — into any
Aurora-edited page. A fragment is *not* content: it is an HTML file shipped
by an add-on (usually the site's theme/brand package), registered under an
id and a title, picked by editors from a list, and rendered exactly as it
is in the file.

Typical uses: a contact box, a badge or seal, a call-to-action banner, a
partner-logo strip — any piece of the design that should be insertable
as-is, maintained by developers in one file, and updated everywhere on the
next deployment.

## How it works

**Aurora-first.** The registration mechanism is the shared
`@plone/registry` singleton — the same `config` object every Aurora block
add-on's install function receives, in Aurora proper and in the Blicca
editor alike. A provider add-on registers one utility per fragment; the
fragment block enumerates them for its sidebar picker
(`type: collective.fragmentsblock.fragment`) and its view renders the
record's `html` client-side, as-is. No server round-trip, no derived
fields, no transformers.

**Templates, when needed.** The markup may contain `${name}` tokens,
filled from the block's persisted `variables` mapping — missing variables
render as empty strings and every value is HTML-escaped. Markup without
tokens passes through byte-for-byte. Values arrive as JSON and are coerced
identically on both surfaces:

| Value | Renders as |
| --- | --- |
| string | itself |
| `true` / `false` | `true` / `false` |
| number | JavaScript's spelling (`1.0` → `1`, `2.5` → `2.5`) |
| `null`, missing | empty |
| array, object | empty (unsupported) |

A variable is always escaped, so it can never inject markup. The
**fragment file itself is trusted code**, not sanitized content: it is
shipped by an add-on, and a `<script>` in it executes on the published
page (the editor's client-side rendering leaves it inert — one more reason
to keep fragments declarative).

> **Known limit.** There is no editor UI for variables yet: a block's
> `variables` mapping is settable through the REST API or a migration, and
> renders correctly on both surfaces, but the sidebar offers only the
> fragment picker. Giving fragments a declared variable schema (and with
> it generated sidebar fields) is the natural next step; until then, a
> fragment whose values differ per placement is better shipped as one
> fragment per variant.

**Blicca classic pages.** The server renderer `@@aurora-block-fragment`
renders the same file through a named `IFragmentsProvider` utility, with
identical substitution semantics — one file, two renderers, parity by
construction. Both surfaces wrap the markup in a single
`<div class="block-fragment">`; the fragment's own root element sits
inside it, so mockup HTML written for a grid or flex parent needs that
wrapper accounted for.

**Fail-soft.** An unknown id, an uninstalled provider, or a
traversal-shaped id degrades to an invisible
`block-fragment-unresolved` placeholder — never a broken page. In the
editor the gap is shown honestly instead.

## Providing fragments

A provider add-on keeps its fragments as plain HTML files in one folder of
its Python package — the single source both halves read:

```
src/my/theme/
├── fragments/
│   └── contact-box.html      ← verbatim from the design mockup
└── fragments.py
```

**Editor half** — in the add-on's Aurora install function (its
`bundle-src` imports the same files via Vite `?raw`):

```ts
import contactBox from '../../src/my/theme/fragments/contact-box.html?raw';

export default function install(config) {
  config.registerUtility({
    type: 'collective.fragmentsblock.fragment',
    name: 'contact-box',
    method: { id: 'contact-box', title: 'Contact box', html: contactBox },
  });
  return config;
}
```

The record's `id` must equal the registration name (enumeration drops
utility names) and must be a slug matching
`^[A-Za-z0-9][A-Za-z0-9_-]*$` — the server resolves it to `<id>.html`, so
a dotted or spaced id would work in the editor and resolve to nothing on
a published page. Records that break the rule are dropped from the picker
with a console warning rather than silently. `title` is the picker label,
and the list is sorted by it.

Ids share **one flat, site-wide namespace** across all providers: the
server asks providers in utility-name order and takes the first hit, and
the client-side registry is keyed by name, so a second provider reusing an
id shadows the first. Prefix them if a site may install several providers.

Registering through the raw registry needs no dependency on this package;
the npm package `@plone-collective/aurora-fragment-block` also exports
`registerFragment(config, record)`, which throws on a missing field or an
invalid id instead of failing later.

> **Rebuild the provider's bundle after editing a fragment file.** The
> classic renderer re-reads the file on every render, but the editor half
> inlines it at build time through the `?raw` import — shipping only the
> changed `.html` leaves the two surfaces disagreeing until `pnpm build`
> runs in the provider's `bundle-src`.

**Server half** — one named utility over the same folder:

```python
# my/theme/fragments.py
from pathlib import Path
from collective.fragmentsblock.fragments import FragmentsFolder

provider = FragmentsFolder(Path(__file__).parent / "fragments")
```

```xml
<utility
    name="my.theme"
    provides="collective.fragmentsblock.interfaces.IFragmentsProvider"
    component="my.theme.fragments.provider"
    />
```

## Using the block

Editors insert a **Fragment** block via the slash menu and choose the
fragment in the block settings — the list shows every registered
fragment's title. That's all; the markup renders immediately (it's already
in the browser), and a redeployed fragment file updates every page
embedding it.

The picker is a plain schema field carrying `choices`, so it renders as a
select wherever the host registers a widget for that slot (Blicca does).
A host that registers none degrades the field to a text input — the block
still works, the editor just types the fragment id.

## Repository layout

One repo, two ecosystems, per the Blicca block add-on contract
(`docs/design/aurora-block-addon-contract.md` and
`docs/adr/0013-block-addons-extension-point.md` in
`plone.blicca.auroraeditor`, which the `§` references in this package's
docstrings point at):

- `src/collective/fragmentsblock/` — the Plone add-on: the
  `@@aurora-block-fragment` server renderer, the `IFragmentsProvider`
  registration point, GenericSetup profiles with the `IAuroraBlockAddon`
  registry record, and the **committed** editor bundle under `static/`
  (no Node needed at install time).
- `bundle-src/` — the editor half, a standalone Aurora block npm package
  (`@plone-collective/aurora-fragment-block`, to be released to npm): the
  block registration, the fragment registry conventions, and the
  substitution renderer. The canonical Vite library build keeps the shared
  singletons (`react`, `@plone/registry`, …) external and emits the
  scope-wrapped CSS in the same build.

## Installation

Add `collective.fragmentsblock` to your project dependencies and install it
via the Plone add-ons control panel. Requires Plone >= 6.0, Python >= 3.10
and `plone.blicca.auroraeditor` >= 1.0.0a2 (block-api 1.0).

## Development

Rebuild the committed editor bundle after changing `bundle-src/`:

```shell
cd bundle-src
pnpm install
pnpm build   # -> static/fragment-block.{js,js.map,css} in the Python package
pnpm test    # vitest suite for the registry conventions and renderers
```

Run the tests from the Plone project environment that has this package
installed as an editable source:

```shell
uv run --no-sync pytest sources/collective.fragmentsblock
```

## License

The project is licensed under GPLv2 (the npm package under MIT).
