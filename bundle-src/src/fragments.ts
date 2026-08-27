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
  description?: string;
};

type Registry = {
  registerUtility: (options: {
    type: string;
    name: string;
    method: unknown;
  }) => void;
  getUtility: (options: { type: string; name: string }) => { method?: unknown };
  getUtilities: (options: { type: string }) => Array<{ method?: unknown }>;
};

export function registerFragment(config: Registry, record: FragmentRecord) {
  if (!record?.id || !record.title || typeof record.html !== 'string') {
    throw new Error(
      'registerFragment: a fragment record needs id, title and html',
    );
  }
  config.registerUtility({
    type: FRAGMENT_UTILITY_TYPE,
    name: record.id,
    method: record,
  });
}

function asRecord(utility: { method?: unknown } | undefined) {
  const record = utility?.method as FragmentRecord | undefined;
  return record && record.id && typeof record.html === 'string'
    ? record
    : null;
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
// HTML-escaped.
const TOKEN = /\$\{([A-Za-z_][A-Za-z0-9_]*)\}/g;

function escapeHtml(value: unknown): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

export function renderFragmentHtml(
  record: FragmentRecord,
  variables?: Record<string, unknown> | null,
): string {
  const values = variables && typeof variables === 'object' ? variables : {};
  return record.html.replace(TOKEN, (_match, name: string) =>
    values[name] == null ? '' : escapeHtml(values[name]),
  );
}
