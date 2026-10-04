// The fragment registry conventions (editor side). A fragment is a static
// piece of markup — typically cut verbatim from a design mockup — that
// provider add-ons register into the shared `@plone/registry` singleton
// from their install function. The fragment block enumerates and renders
// these records; nothing about a fragment lives in Plone content.
//
// `getUtilities` returns records without their registration names, so the
// record itself must carry its `id` (kept equal to the registration name).

export const FRAGMENT_UTILITY_TYPE = 'collective.fragmentsblock.fragment';

export type FragmentRecord = {
  /** Registration name; the value stored on the block node. */
  id: string;
  /** Label shown in the block's fragment picker. */
  title: string;
  /** The fragment markup, injected as-is apart from `${var}` tokens. */
  html: string;
};

type Registry = {
  /** The host's mount options land here; `apiPath` is the portal URL. */
  settings?: { apiPath?: string };
  registerUtility: (options: {
    type: string;
    name: string;
    method: unknown;
  }) => void;
  getUtility: (options: { type: string; name: string }) => { method?: unknown };
  getUtilities: (options: { type: string }) => Array<{ method?: unknown }>;
};

// Ids are slugs on both sides: the server resolves them to `<id>.html`
// inside the provider's directory, so anything else is a path it must
// refuse. Enforced here too — an id the editor accepts but the server
// rejects would render in the editor and vanish on the published page.
export const FRAGMENT_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;

export function registerFragment(config: Registry, record: FragmentRecord) {
  if (!record?.id || !record.title || typeof record.html !== 'string') {
    throw new Error(
      'registerFragment: a fragment record needs id, title and html',
    );
  }
  if (!FRAGMENT_ID_RE.test(record.id)) {
    throw new Error(
      `registerFragment: ${JSON.stringify(record.id)} is not a valid ` +
        'fragment id (must match /^[A-Za-z0-9][A-Za-z0-9_-]*$/, because ' +
        'the server resolves it to a filename)',
    );
  }
  config.registerUtility({
    type: FRAGMENT_UTILITY_TYPE,
    name: record.id,
    method: record,
  });
}

// Registrations made through the bare registry (no dependency on this
// package) are validated on read instead: a record the server could never
// resolve must not reach the picker, and a malformed one is dropped with a
// warning rather than silently.
function asRecord(utility: { method?: unknown } | undefined) {
  const record = utility?.method as FragmentRecord | undefined;
  if (!record || typeof record.html !== 'string' || !record.title) return null;
  if (typeof record.id !== 'string' || !FRAGMENT_ID_RE.test(record.id)) {
    console.warn(
      'collective.fragmentsblock: ignoring a fragment record with an ' +
        'invalid id:',
      record?.id,
    );
    return null;
  }
  return record;
}

export function getFragment(
  config: Registry,
  id: unknown,
): FragmentRecord | null {
  if (typeof id !== 'string' || !id) return null;
  return asRecord(config.getUtility({ type: FRAGMENT_UTILITY_TYPE, name: id }));
}

export function listFragments(config: Registry): FragmentRecord[] {
  return config
    .getUtilities({ type: FRAGMENT_UTILITY_TYPE })
    .map(asRecord)
    .filter((record): record is FragmentRecord => record !== null)
    .sort((a, b) => a.title.localeCompare(b.title));
}

// ${var} substitution — the "template" half. Semantics are mirrored 1:1 by
// the server renderer (fragments.py substitute()): values come from the
// block's persisted `variables` mapping (so both surfaces see identical
// input), missing variables become empty strings, every value is
// HTML-escaped. Keep the two implementations readable side by side —
// parity is the whole point, and only trivial rules stay checkable.
const TOKEN = /\$\{([A-Za-z_][A-Za-z0-9_]*)\}/g;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// The coercion table both halves implement. Anything outside it (arrays,
// objects) renders empty rather than as a JS-flavoured or Python-flavoured
// string — `[object Object]` and `{'k': 1}` are equally useless, and
// disagreeing about which to emit is worse than emitting neither.
function coerce(value: unknown): string {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '';
  return '';
}

export function renderFragmentHtml(
  record: FragmentRecord,
  variables?: Record<string, unknown> | null,
): string {
  const values = variables && typeof variables === 'object' ? variables : {};
  return record.html.replace(TOKEN, (_match, name: string) =>
    // hasOwn, not `values[name]`: a token named like an Object.prototype
    // member (${toString}, ${constructor}) would otherwise resolve to the
    // inherited member here and to nothing on the server.
    Object.hasOwn(values, name) ? escapeHtml(coerce(values[name])) : '',
  );
}

// --- Loading from the server (ADR 0002) ---------------------------------
//
// The fragments are files in provider add-ons, enumerated by the server's
// `@fragments` service. The block's install() calls this before the editor's
// first render (the host awaits install, block-api 1.2), so nothing a theme
// ships for the editor exists any more — no bundle, no record, no rebuild.
// The request rides the session cookie: the editor page is served by Plone
// on the same origin, and the service is readable by whoever may view the
// site, like the pages that render the same markup.

export const FRAGMENTS_SERVICE = '@fragments';

type FetchLike = (
  input: string,
  init?: { headers?: Record<string, string>; credentials?: 'same-origin' },
) => Promise<{ ok: boolean; status: number; json: () => Promise<unknown> }>;

export async function loadFragments(
  config: Registry,
  fetchImpl: FetchLike = (input, init) => fetch(input, init),
): Promise<FragmentRecord[]> {
  const base = (config.settings?.apiPath ?? '').replace(/\/+$/, '');
  const response = await fetchImpl(`${base}/${FRAGMENTS_SERVICE}`, {
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
  });
  if (!response.ok) {
    throw new Error(`${FRAGMENTS_SERVICE} answered ${response.status}`);
  }
  const body = (await response.json()) as { items?: unknown } | null;
  const items = Array.isArray(body?.items) ? body.items : [];
  const registered: FragmentRecord[] = [];
  for (const item of items) {
    try {
      registerFragment(config, item as FragmentRecord);
      registered.push(item as FragmentRecord);
    } catch (error) {
      console.warn(
        'collective.fragmentsblock: dropping a fragment the server sent:',
        error,
      );
    }
  }
  return registered;
}

// Whether the load failed. The edit placeholder tells a fragment that could
// not be loaded apart from one that is not registered: the first is a page
// reload away, the second is an uninstalled add-on.
let loadError: unknown = null;

export function setFragmentsLoadError(error: unknown) {
  loadError = error;
}

export function getFragmentsLoadError(): unknown {
  return loadError;
}
