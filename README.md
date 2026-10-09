# collective.fragmentsblock

A **Fragment** block for the Aurora editor in [Plone](https://plone.org) Blicca.

A fragment is a static piece of HTML, usually cut straight from the design
mockup: a contact box, a seal, a call-to-action banner, a partner-logo
strip. Your theme ships it as a file in a folder it registers with one line
of ZCML. Editors then pick it from a list and drop it into a page. The
markup is rendered exactly as it is in the file, both in the editor and on
published pages.

Editors never edit the markup. When the file changes, every page using the
fragment updates on the next deployment.

## Installation

Add `collective.fragmentsblock` to your project dependencies and install it
in the Plone add-ons control panel.

Requirements: Plone 6, Python 3.10 or newer, and a `plone.blicca.auroraeditor`
that ships block-api 2.0, the Plate 53 editor. The editor waits for this
block to fetch its fragments before it renders.

This package only provides the block. Fragments come from your own add-on,
typically the theme package. See the next section.

## Register a fragment

Fragments live in a folder of your add-on, one HTML file per fragment. The
server reads the files when it renders classic pages, and the editor fetches
the same files from the server when it opens. Nothing is built, bundled or
copied.

```
src/my/theme/
├── fragments/
│   ├── contact-box.html
│   └── seal.html
└── configure.zcml
```

The file name is the fragment id. Ids must match `^[A-Za-z0-9][A-Za-z0-9_-]*$`
and are unique across the whole site, so prefix them if more than one
add-on may provide fragments. A file whose name is not a valid id is skipped
with a warning.

Register the folder in your `configure.zcml`:

```xml
<!-- my/theme/configure.zcml -->
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:fragments="http://namespaces.plone.org/fragmentsblock">

  <include package="collective.fragmentsblock" file="meta.zcml" />

  <fragments:folder directory="fragments" />

</configure>
```

`directory` is relative to your package. The folder is registered under
your package name. Pass `name="..."` if you need another one. A folder that
does not exist is an error at startup, not an empty picker.

That is all. Restart Plone and the fragments appear in the picker.

### Titles

Editors pick a fragment by its title. Put it in a comment on the first line
of the file:

```html
<!-- title: Contact box -->
<aside class="contact-box">
  ...
</aside>
```

Without that comment the title is derived from the file name:
`contact-box.html` becomes "Contact box", `partner_logos.html` becomes
"Partner logos". The comment is part of the markup and is rendered with it;
browsers ignore it.

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
- **The editor fetches `@fragments`.** When the editor opens, the fragment
  block requests `<site>/@fragments` with the session cookie and registers
  what comes back before the first render. The list is every provider's
  `records()`; where two providers use the same id, the one whose name sorts
  first wins, on both surfaces. If the request fails, the block stays
  available with an empty picker and existing fragment blocks say so instead
  of rendering nothing.
- **Other sources.** A folder of files is the stock provider. For anything
  else, register a named utility that implements `IFragmentsProvider`:
  `get(fragment_id)` returns the HTML or `None`, and `records()` lists every
  fragment as `{"id", "title", "html"}`.
- **Registering from JavaScript still works.** An Aurora add-on may register
  fragments itself, with `registerFragment(config, {id, title, html})` from
  the npm package `@plone-collective/aurora-fragment-block` or with a bare
  `config.registerUtility` of type `collective.fragmentsblock.fragment`. The
  server then needs a matching provider, or the fragment renders only in the
  editor.

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

Maik Derstappen, [derico.de](https://derico.de), <md@derico.de>
