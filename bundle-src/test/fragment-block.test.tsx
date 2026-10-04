/**
 * Tests for the registry-based fragment model: registration conventions,
 * ${var} substitution (semantics mirrored by the server's fragments.py),
 * and the block components' fail-soft rendering.
 */
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import config from '@plone/registry';
import install, {
  FRAGMENT_UTILITY_TYPE,
  getFragment,
  getFragmentsLoadError,
  listFragments,
  loadFragments,
  registerFragment,
  renderFragmentHtml,
} from '../src/index';
import { setFragmentsLoadError } from '../src/fragments';
import FragmentBlockView from '../src/FragmentBlockView';
import FragmentBlockEdit from '../src/FragmentBlockEdit';

const CONTACT_BOX = {
  id: 'contact-box',
  title: 'Contact box',
  html: '<aside class="contact-box"><h2>Contact</h2><p>${phone}</p></aside>',
};

const jsonResponse = (body: unknown, status = 200) => ({
  ok: status < 400,
  status,
  json: async () => body,
});

// What the server answers by default: an empty list. Tests about the load
// itself replace it; everything else registers fragments directly.
let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  (config as any).blocks.blocksConfig = {};
  (config as any)._utilities[FRAGMENT_UTILITY_TYPE] = {};
  (config as any)._utilities.styleFieldDefinition = {};
  (config as any).settings = { apiPath: 'http://plone' };
  setFragmentsLoadError(null);
  fetchMock = vi.fn(async () => jsonResponse({ items: [] }));
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// The host's background palette: a `styleFieldDefinition` utility named
// after the style field (Blicca registers exactly this in its bootstrap).
const registerBackgroundPalette = () =>
  (config as any).registerUtility({
    type: 'styleFieldDefinition',
    name: 'backgroundColor',
    method: () => [
      { name: 'none', label: 'None', style: {} },
      { name: 'grey', label: 'Grey', style: { '--block-background': '#eee' } },
    ],
  });

describe('fragment registry conventions', () => {
  it('registers and resolves a fragment record', async () => {
    registerFragment(config, CONTACT_BOX);
    expect(getFragment(config, 'contact-box')).toEqual(CONTACT_BOX);
    expect(getFragment(config, 'nope')).toBeNull();
    expect(getFragment(config, undefined)).toBeNull();
  });

  it('rejects incomplete records', async () => {
    expect(() =>
      registerFragment(config, { id: 'x', title: 'X' } as any),
    ).toThrow(/id, title and html/);
  });

  it('rejects ids the server could never resolve to a file', async () => {
    for (const id of ['../secret', 'a/b', 'Contact Box', 'my.contact', '_x']) {
      expect(() =>
        registerFragment(config, { id, title: 'X', html: '<b/>' }),
      ).toThrow(/not a valid fragment id/);
    }
  });

  it('drops raw registrations with an invalid id instead of listing them', async () => {
    (config as any).registerUtility({
      type: FRAGMENT_UTILITY_TYPE,
      name: 'my.contact',
      method: { id: 'my.contact', title: 'Bad id', html: '<b/>' },
    });
    expect(listFragments(config)).toEqual([]);
    expect(getFragment(config, 'my.contact')).toBeNull();
  });

  it('accepts raw registerUtility registrations (the bare convention)', async () => {
    (config as any).registerUtility({
      type: FRAGMENT_UTILITY_TYPE,
      name: 'contact-box',
      method: CONTACT_BOX,
    });
    expect(getFragment(config, 'contact-box')).toEqual(CONTACT_BOX);
  });

  it('lists fragments sorted by title, skipping malformed records', async () => {
    registerFragment(config, CONTACT_BOX);
    registerFragment(config, { id: 'banner', title: 'Banner', html: '<b/>' });
    (config as any).registerUtility({
      type: FRAGMENT_UTILITY_TYPE,
      name: 'broken',
      method: { title: 'No id or html' },
    });
    expect(listFragments(config).map((r) => r.id)).toEqual([
      'banner',
      'contact-box',
    ]);
  });
});

describe('renderFragmentHtml', () => {
  it('passes markup through verbatim without variables', async () => {
    const record = { id: 'x', title: 'X', html: '<div class="a">&amp; ok</div>' };
    expect(renderFragmentHtml(record)).toBe('<div class="a">&amp; ok</div>');
  });

  // The mirror image of TestCoerceParity in
  // src/collective/fragmentsblock/tests/test_fragments.py — the two files
  // are the parity contract, so keep the cases aligned.
  it('coerces booleans, numbers and containers like the server', async () => {
    const t = (value: unknown) =>
      renderFragmentHtml({ id: 'x', title: 'X', html: '${v}' }, { v: value });
    expect(t(true)).toBe('true');
    expect(t(false)).toBe('false');
    expect(t(0)).toBe('0');
    expect(t(-42)).toBe('-42');
    expect(t(1.0)).toBe('1');
    expect(t(2.5)).toBe('2.5');
    expect(t(['a', 'b'])).toBe('');
    expect(t({ k: 1 })).toBe('');
    expect(t(Number.NaN)).toBe('');
  });

  it('does not resolve tokens through the prototype chain', async () => {
    const record = { id: 'x', title: 'X', html: '${toString}${constructor}' };
    expect(renderFragmentHtml(record, {})).toBe('');
    expect(renderFragmentHtml({ ...record, html: '${toString}' }, { toString: 'x' })).toBe('x');
  });

  it('substitutes ${var} tokens HTML-escaped, missing ones as empty', async () => {
    expect(
      renderFragmentHtml(CONTACT_BOX, { phone: '<b>+49 & 30</b>' }),
    ).toContain('<p>&lt;b&gt;+49 &amp; 30&lt;/b&gt;</p>');
    expect(renderFragmentHtml(CONTACT_BOX)).toContain('<p></p>');
    expect(renderFragmentHtml(CONTACT_BOX, { phone: null })).toContain(
      '<p></p>',
    );
  });
});

describe('block components', () => {
  it('view renders the fragment markup as-is', async () => {
    registerFragment(config, CONTACT_BOX);
    const out = renderToStaticMarkup(
      <FragmentBlockView data={{ fragment: 'contact-box', variables: { phone: '030' } }} />,
    );
    expect(out).toContain('class="block-fragment"');
    expect(out).toContain('<aside class="contact-box"><h2>Contact</h2><p>030</p></aside>');
  });

  // The editor names a block by `data-block-summary` where the block renders
  // no text of its own (block add-on contract §1.6) — which is the normal
  // case for a fragment, and the only thing that tells two of them apart in
  // the drag rows, where the label is the constant "Fragment".
  it('view names itself with the fragment title', async () => {
    registerFragment(config, CONTACT_BOX);
    const out = renderToStaticMarkup(
      <FragmentBlockView data={{ fragment: 'contact-box' }} />,
    );
    expect(out).toContain('data-block-summary="Contact box"');
  });

  it('view fails soft to the invisible placeholder', async () => {
    const out = renderToStaticMarkup(
      <FragmentBlockView data={{ fragment: 'gone' }} />,
    );
    expect(out).toBe('<div class="block-fragment block-fragment-unresolved"></div>');
  });

  it('edit shows honest placeholders for unchosen and unregistered', async () => {
    const empty = renderToStaticMarkup(
      <FragmentBlockEdit data={{}} block="b" selected={false} setBlock={() => {}} />,
    );
    expect(empty).toContain('Choose a fragment');
    const gone = renderToStaticMarkup(
      <FragmentBlockEdit data={{ fragment: 'gone' }} block="b" selected={false} setBlock={() => {}} />,
    );
    expect(gone).toContain('not registered');
  });

  it('install registers the block and its schema enumerates fragments', async () => {
    registerFragment(config, CONTACT_BOX);
    await install(config);
    const entry = (config as any).blocks.blocksConfig.fragment;
    expect(entry.id).toBe('fragment');
    const schema = entry.blockSchema();
    expect(schema.properties.fragment.choices).toEqual([
      ['', '— Choose a fragment —'],
      ['contact-box', 'Contact box'],
    ]);
    expect(schema.required).toEqual(['fragment']);
  });
});

// Width and background are Aurora *style fields*: declaring the schema
// property is the whole of the wiring, since StyleFieldsKit (editor) and
// plate.py (server) stamp the class and custom properties on the block
// wrapper generically. So what there is to test is the declaration.
describe('style fields', () => {
  it('offers the width control, defaulting to the width it renders at now', async () => {
    await install(config);
    const schema = (config as any).blocks.blocksConfig.fragment.blockSchema();
    expect(schema.fieldsets[0].fields).toContain('blockWidth');
    expect(schema.properties.blockWidth).toEqual({
      title: 'Block width',
      widget: 'width',
      default: 'default',
      styleField: true,
    });
  });

  it('never declares defaultBlockWidth alongside the field', async () => {
    // Contract §1.4: a schema style field wins over defaultBlockWidth, so
    // declaring both is a contradiction that silently drops the default.
    await install(config);
    expect(
      (config as any).blocks.blocksConfig.fragment.defaultBlockWidth,
    ).toBeUndefined();
  });

  it('offers the background slots the host registered', async () => {
    registerBackgroundPalette();
    await install(config);
    const schema = (config as any).blocks.blocksConfig.fragment.blockSchema();
    expect(schema.fieldsets[0].fields).toContain('backgroundColor');
    expect(schema.properties.backgroundColor).toEqual({
      title: 'Background',
      choices: [
        ['none', 'None'],
        ['grey', 'Grey'],
      ],
      default: 'none',
      styleField: true,
    });
  });

  it('omits the background field when the host registers no palette', async () => {
    await install(config);
    const schema = (config as any).blocks.blocksConfig.fragment.blockSchema();
    expect(schema.fieldsets[0].fields).not.toContain('backgroundColor');
    expect(schema.properties.backgroundColor).toBeUndefined();
  });

  it('only ever defaults to the neutral slot', async () => {
    // Any other default would paint every fragment block ever inserted; a
    // palette without a `none` gets no default, and an unresolved value
    // contributes no style — which is the same unpainted block.
    (config as any).registerUtility({
      type: 'styleFieldDefinition',
      name: 'backgroundColor',
      method: () => [{ name: 'grey', label: 'Grey', style: {} }],
    });
    await install(config);
    const schema = (config as any).blocks.blocksConfig.fragment.blockSchema();
    expect(schema.properties.backgroundColor.choices).toEqual([
      ['grey', 'Grey'],
    ]);
    expect(schema.properties.backgroundColor).not.toHaveProperty('default');
  });

  it('reads the palette lazily, not at install time', async () => {
    // The host bootstraps before add-on installs today, but the picker is
    // built lazily for the same reason and both must survive the reverse.
    await install(config);
    registerBackgroundPalette();
    const schema = (config as any).blocks.blocksConfig.fragment.blockSchema();
    expect(schema.properties.backgroundColor.choices).toHaveLength(2);
  });
});

// The fragments come from the server (ADR 0002): install() fetches
// `@fragments` and registers what it answers before the host renders.
describe('loading from the server', () => {
  const SEAL = { id: 'seal', title: 'Seal of approval', html: '<figure/>' };

  it('install fetches @fragments under apiPath and registers the items', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ items: [CONTACT_BOX, SEAL] }));
    expect(await install(config)).toBe(config);
    expect(fetchMock).toHaveBeenCalledWith('http://plone/@fragments', {
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    });
    expect(listFragments(config).map((r) => r.id)).toEqual(['contact-box', 'seal']);
    expect(getFragment(config, 'seal')).toEqual(SEAL);
    expect(getFragmentsLoadError()).toBeNull();
  });

  it('tolerates a trailing slash on apiPath', async () => {
    (config as any).settings = { apiPath: 'http://plone/' };
    await loadFragments(config as any);
    expect(fetchMock.mock.calls[0][0]).toBe('http://plone/@fragments');
  });

  it('drops an item the server got wrong and keeps the rest', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    fetchMock.mockResolvedValue(
      jsonResponse({
        items: [{ id: 'my.bad', title: 'Bad id', html: '<b/>' }, SEAL, { id: 'x' }],
      }),
    );
    const registered = await loadFragments(config as any);
    expect(registered).toEqual([SEAL]);
    expect(listFragments(config).map((r) => r.id)).toEqual(['seal']);
    expect(warn).toHaveBeenCalledTimes(2);
  });

  it('keeps the block and records the failure when the request fails', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    fetchMock.mockRejectedValue(new TypeError('network down'));
    expect(await install(config)).toBe(config);
    expect((config as any).blocks.blocksConfig.fragment.id).toBe('fragment');
    expect(listFragments(config)).toEqual([]);
    expect(String(getFragmentsLoadError())).toContain('network down');
    expect(warn).toHaveBeenCalledTimes(1);
  });

  it('treats an error response as a failed load', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    fetchMock.mockResolvedValue(jsonResponse({ error: 'nope' }, 500));
    await install(config);
    expect(String(getFragmentsLoadError())).toContain('answered 500');
  });

  it('edit tells a failed load apart from an unregistered fragment', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    fetchMock.mockRejectedValue(new Error('down'));
    await install(config);
    const failed = renderToStaticMarkup(
      <FragmentBlockEdit data={{ fragment: 'seal' }} block="b" selected={false} setBlock={() => {}} />,
    );
    expect(failed).toContain('could not be loaded');
    expect(failed).not.toContain('not registered');

    fetchMock.mockResolvedValue(jsonResponse({ items: [] }));
    await install(config);
    const gone = renderToStaticMarkup(
      <FragmentBlockEdit data={{ fragment: 'seal' }} block="b" selected={false} setBlock={() => {}} />,
    );
    expect(gone).toContain('not registered');
  });
});
