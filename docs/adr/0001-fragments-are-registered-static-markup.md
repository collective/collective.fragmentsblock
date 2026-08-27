# Fragments are registered static markup, not content objects

A *fragment* is a piece of a design mockup — a contact box, a badge, a
call-to-action banner — that editors should be able to drop into a page
as-is. The obvious first reading of "reusable snippet" is "centrally
maintained **content**", and the ecosystem survey in
`docs/research/snippet-blocks-existing-solutions.md` (site repository)
recommended exactly that: store an `href` to a blocks-enabled Document,
inject the target's enriched somersault value with a restapi transformer,
re-render it client-side — the Volto teaser's reference semantics applied
to whole pages.

That answered a different question. The material an integrator wants to
reuse is the **markup handed over with the design** — HTML that must land
on the page byte-for-byte, that is versioned and deployed with the theme,
and that no editor should be able to break. Modelling it as content forces
the design through the block round-trip (author it in Aurora, hope the
renderer reproduces it), makes it site data rather than deployable code,
and buys editorial workflow nobody asked for.

## Decision

**A fragment is a static HTML file shipped by a provider add-on, published
into the shared `@plone/registry` singleton under an id and a title. The
fragment block stores only that id and renders the registered markup
as-is; `${name}` tokens are the only dynamic element, filled from the
block's own `variables` mapping.**

1. **Registration is `@plone/registry`, not content, not the ZODB.** A
   provider registers one utility per fragment
   (`type: collective.fragmentsblock.fragment`, `method: {id, title,
   html}`) from its Aurora install function, importing the mockup file
   with Vite `?raw`. That is the one registration mechanism available
   verbatim in Aurora proper *and* in the Blicca editor, which makes the
   block Aurora-first as the block add-on contract §1.1 requires. The
   record carries its own `id` because `getUtilities` returns records
   without their registration names.

   Rejected: a Plone registry (`plone.app.registry`) record set, and a
   ZCML-registered fragments *directory* as the primary mechanism. Both
   are server-side, so the editor would need a fetch to enumerate or
   render anything — a round-trip for markup the browser could already
   have, and a second source of truth to keep in sync.

2. **Metadata is the registry record.** The title lives in the record, not
   in front matter inside the `.html` file and not in a sidecar. The file
   therefore stays exactly what the designer delivered: valid, unannotated
   mockup HTML that other tools can open.

3. **Templating is `${name}` substitution, not TAL/Chameleon.** Page
   Templates would render only on the server, which contradicts (1). The
   substitution is deliberately minimal — HTML-escaped values, missing
   variables as empty strings, a short coercion table for the JSON types —
   and is implemented twice, in `bundle-src/src/fragments.ts` and in
   `fragments.py`, as the price of having both surfaces render the same
   file. Where the two languages disagree (`str(True)` vs `String(true)`,
   integral floats, containers) the JavaScript spelling wins, because the
   editor cannot produce any other one. Anything richer than token
   replacement must be a block of its own, not a template language
   re-implemented in two runtimes.

4. **Ids are slugs, enforced on both sides.** The server resolves an id to
   `<id>.html` inside the provider's directory, so an id it cannot resolve
   must not reach the editor's picker either — a fragment that renders on
   the canvas and vanishes when published is the one failure mode fail-soft
   placeholders cannot explain.

5. **Classic rendering reads the same file** through a named
   `IFragmentsProvider` utility (`FragmentsFolder` over the provider's
   directory), so a provider keeps its fragments in one place and the two
   halves cannot drift apart in content — only, if the implementations
   diverge, in substitution. That parity is covered by tests on both
   sides.

6. **Fail-soft.** An id whose provider is not installed, or one shaped
   like a path traversal, renders the invisible
   `block-fragment-unresolved` placeholder rather than an error or a file
   read outside the fragments directory.

## Consequences

- **Fragments are deployed, not edited.** Changing one is a code change in
  the provider add-on and takes a release; editors choose among fragments,
  they never author them. This is the intended trade: the design stays
  intact.
- **No transformers, no cycle guard, no server round-trip.** The editor
  has the markup in hand, so the block renders instantly and stores
  nothing derived. The whole client-side somersault renderer the previous
  design needed is gone.
- **Duplicated substitution logic** in TypeScript and Python is a standing
  parity obligation; keep it trivial enough that parity stays checkable by
  reading both functions side by side. The paired test cases
  (`TestCoerceParity` and the coercion test in the vitest suite) are the
  contract's teeth — extend both or neither.
- **Fragments are trusted, executable code.** They ship with an add-on, so
  a `<script>` in one runs on the published page — the mechanism deploys
  developer-authored markup and sanitizes nothing. (The editor's
  client-side rendering leaves such a script inert, which makes a
  script-bearing fragment a parity trap as well as a smell.)
- **Escaped variables only.** A variable can never inject markup. A
  fragment needing a variable *region* of HTML wants a block, or a
  dedicated fragment per variant.
- **Variables have no editor UI in this version.** Values are settable
  through the REST API or a migration and render on both surfaces, but the
  sidebar shows only the picker. Generating sidebar fields needs the
  fragment record to *declare* its variables, which is deliberately
  deferred until real fragments show what the declarations must express.
- **Embedding live content is out of scope.** If reusable *content* is
  ever wanted, it is a separate block (the teaser's reference semantics
  applied to a page) and does not belong in this one.
