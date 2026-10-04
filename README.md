# collective.fragmentsblock

A **Fragment** block for the Aurora editor in [Plone](https://plone.org) Blicca.

A fragment is a static piece of HTML, usually cut straight from the design
mockup: a contact box, a seal, a call-to-action banner, a partner-logo
strip. Your theme ships it as a file and registers it under an id and a
title. Editors then pick it from a list and drop it into a page. The markup
is rendered exactly as it is in the file, both in the editor and on
published pages.

Editors never edit the markup. When the file changes, every page using the
fragment updates on the next deployment.

## Installation

Add `collective.fragmentsblock` to your project dependencies and install it
in the Plone add-ons control panel.

Requirements: Plone 6, Python 3.10 or newer, and `plone.blicca.auroraeditor`
1.0.0a2 or newer.

This package only provides the block. Fragments come from your own add-on,
typically the theme package. See the next section.

## Register a fragment

Fragments live in a folder of your add-on, one HTML file per fragment. Both
the editor and the server read from that same folder.

```
src/my/theme/
├── fragments/
│   └── contact-box.html
├── fragments.py
├── configure.zcml
└── static/
    └── fragments.js       <- built from editor-src/
```

The file name is the fragment id. Ids must match `^[A-Za-z0-9][A-Za-z0-9_-]*$`
and are unique across the whole site, so prefix them if more than one
add-on may provide fragments.

### 1. Server side

Point a `FragmentsFolder` at the folder and register it as a named utility.
The server uses it to render fragments on classic pages.

```python
# my/theme/fragments.py
from pathlib import Path
from collective.fragmentsblock.fragments import FragmentsFolder

provider = FragmentsFolder(Path(__file__).parent / "fragments")
```

```xml
<!-- my/theme/configure.zcml -->
<utility
    name="my.theme"
    provides="collective.fragmentsblock.interfaces.IFragmentsProvider"
    component="my.theme.fragments.provider"
    />

<plone:static
    name="my.theme"
    type="plone"
    directory="static"
    />
```

### 2. Editor side

The editor needs the same fragments in the browser. Ship a small ES module
whose default export registers one utility per fragment. Import the HTML
files with Vite's `?raw` so the file stays the single source:

```ts
// editor-src/index.ts
import contactBox from '../src/my/theme/fragments/contact-box.html?raw';

export default function install(config) {
  config.registerUtility({
    type: 'collective.fragmentsblock.fragment',
    name: 'contact-box',
    method: { id: 'contact-box', title: 'Contact box', html: contactBox },
  });
  return config;
}
```

`id` must equal the file name without `.html`. `title` is what editors see
in the picker. Build the module to `static/fragments.js` and commit the
output, so no Node is needed at install time.

If you prefer validation at registration time, the npm package
`@plone-collective/aurora-fragment-block` exports
`registerFragment(config, { id, title, html })`, which throws on a missing
field or an invalid id.

### 3. Tell the editor to load your module

Add an Aurora block add-on record to your GenericSetup profile. It points
the editor at the module from step 2. Your add-on registers no block of its
own, so `types` stays empty.

```xml
<!-- profiles/default/registry.xml -->
<records
    interface="plone.blicca.auroraeditor.interfaces.IAuroraBlockAddon"
    prefix="plone.blicca.auroraeditor.blockaddons/my.theme.fragments"
    >
  <value key="bundle">++plone++my.theme/fragments.js</value>
  <value key="block_api">1.0</value>
  <value key="enabled">True</value>
</records>
```

Reinstall or upgrade your add-on and the fragments appear in the picker.

**After editing a fragment file, rebuild the editor module.** The server
reads the file on every render, but the editor module has the HTML inlined
at build time. Until you rebuild, the editor and the published page show
different markup.

## Add a fragment to a page

1. Open the page in the Aurora editor.
2. Type `/` and choose **Fragment** from the slash menu.
3. In the block settings, pick the fragment from the **Fragment** list.

The fragment renders immediately. Two more settings control placement:

- **Block width**: `narrow`, `default`, `layout` or `full`. Defaults to
  `default`.
- **Background**: a named colour slot from your theme's palette, such as
  `Grey` or `Accent`. The field only appears if the theme registers a
  palette.

Both paint the block wrapper around the fragment, not the fragment itself.

If a fragment's add-on gets uninstalled, the editor shows a note in place
of the block and the published page renders nothing there. Pages never
break.

## Good to know

- **Fragment HTML is trusted.** It ships with your add-on and is not
  sanitised. A `<script>` in it runs on the published page.
- **Variables.** Markup may contain `${name}` tokens. They are filled from
  the block's `variables` mapping, HTML-escaped, with missing names
  rendered empty. There is no editor UI for this yet. The mapping can be
  set through the REST API or an upgrade step. For now, if a fragment
  needs different values on different pages, ship one fragment per
  variant.
- **Wrapper.** Both the editor and the server wrap the markup in a
  `<div class="block-fragment">`. Mockup HTML written for a grid or flex
  parent needs to account for that.

## Development

The editor half lives in `bundle-src/` and is built into the Python
package's `static/` folder. The build output is committed.

```shell
cd bundle-src
pnpm install
pnpm build
pnpm test
```

Python tests:

```shell
uv run --extra test pytest
```

## License

GPLv2 for the Python package, MIT for the npm package.

## Author

Maik Derstappen, [derico](https://derico.de), <md@derico.de>