# The editor fetches the fragment list from the server

ADR 0001 made a fragment a file shipped by a provider add-on and published
into the shared `@plone/registry` singleton from the provider's own Aurora
install function, "registry only, no server round-trip". The server half
reads the same file through an `IFragmentsProvider` utility, so the content
could not drift. The cost sat entirely with the provider: to put its files
into the editor it had to ship an ES module importing each file `?raw`, a
`plone:static` directory for the built module, an `IAuroraBlockAddon`
record so `@@aurora-edit` loads it, and a Node build — and it had to rebuild
after every edit, or the editor showed yesterday's markup against today's
published page. The derico theme, the first provider, carried all four plus
lockstep tests holding the editor map against the directory.

The question this answers: can the editor side need no theme work at all?

## Decision

**The fragment block fetches its own list. A `@fragments` REST service on
the site root enumerates every `IFragmentsProvider`'s `records()` as
`[{id, title, html}]`; the block's `install()` fetches it and registers each
record into the registry before the editor's first render. A provider ships
its files and the `fragments:folder` line, nothing else.**

1. **The server enumerates; the registry stays the editor's model.**
   `IFragmentsProvider` gains `records()` beside `get(id)`. The block's
   views, picker and `registerFragment` convention are unchanged; what
   changes is who calls `registerUtility`. An Aurora-side add-on may still
   register fragments itself (it then needs a matching provider, as before).
   Providers are listed in the order `resolve` consults them and the first
   record of an id wins, so a clash resolves the same way on both surfaces.

2. **`install()` is asynchronous, and the host awaits it.** The editor's
   config registry is not reactive, so the records have to land before the
   first render. `plone.blicca.auroraeditor` 1.0.0a3 awaits whatever an
   install returns (block-api 1.2); the record declares 1.2, and an older
   host skips this block fail-soft rather than failing it. A load that fails
   keeps the block: the picker is empty and an existing fragment block says
   the list could not be loaded, which is a reload away, instead of "not
   registered", which is an uninstalled add-on.

3. **The title lives in the file, as an optional first line.**
   `<!-- title: Contact box -->` before any markup; otherwise the title is
   derived from the id (`contact-box` → "Contact box"). ADR 0001 kept the
   title out of the file so the file stayed what the designer delivered.
   That reasoning assumed a JS record to hold it; without one the choice is
   a sidecar, a convention in ZCML, or one comment line. The comment keeps
   the file valid, self-describing and free of companions, and a file
   without it still works.

4. **The request rides the session cookie.** The editor page is served by
   Plone on the same origin and the service is readable by whoever may view
   the site — the same markup is on its public pages. No token plumbing.

Considered and not taken:

- **Host-provided add-on data**: a host extension point collecting JSON
  from named utilities into the mount options, read synchronously by the
  block. No fetch and no await, but every fragment's HTML inlined into every
  edit page's config, and a new host extension interface with its own
  contract and ADR, for one consumer.
- **Generating the theme's module** from its folder with a console script.
  Least invasive, but the static directory, the record and the rebuild
  drift all stay; it moves the work, it does not remove it.

## Consequences

- **A provider is files plus one ZCML line.** No Node, no bundle, no record,
  no rebuild, no lockstep tests; what the server resolves is what the
  editor lists, by construction.
- **One GET per editor open**, cacheable, before the first render. A site
  with many large fragments pays it on every edit; the inline alternative
  would have paid it on every edit too, in the page.
- **The host floor rises** to the version that awaits installs; the record's
  `block_api` 1.2 keeps the bundle off older hosts (upgrade step 1001).
- **ADR 0001 is amended, not replaced.** Fragments are still deployed files
  rendered as-is, the registry is still the editor's model, substitution
  parity still holds. Only its "no server round-trip" and "title in the JS
  record" no longer hold.
- **The comment line is rendered.** The server emits the file byte for
  byte and the editor renders what the server lists, so the title comment
  appears in the published HTML. Inert, and parity is worth more than one
  stripped line.
