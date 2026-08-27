/**
 * Tests for the registry-based fragment model: registration conventions,
 * ${var} substitution (semantics mirrored by the server's fragments.py),
 * and the block components' fail-soft rendering.
 */
import { renderToStaticMarkup } from 'react-dom/server';
import { beforeEach, describe, expect, it } from 'vitest';
import config from '@plone/registry';
import install, {
  FRAGMENT_UTILITY_TYPE,
  getFragment,
  listFragments,
  registerFragment,
  renderFragmentHtml,
} from '../src/index';
import FragmentBlockView from '../src/FragmentBlockView';
import FragmentBlockEdit from '../src/FragmentBlockEdit';

const CONTACT_BOX = {
  id: 'contact-box',
  title: 'Contact box',
  html: '<aside class="contact-box"><h2>Contact</h2><p>${phone}</p></aside>',
};

beforeEach(() => {
  (config as any).blocks.blocksConfig = {};
  (config as any)._utilities[FRAGMENT_UTILITY_TYPE] = {};
});

describe('fragment registry conventions', () => {
  it('registers and resolves a fragment record', () => {
    registerFragment(config, CONTACT_BOX);
    expect(getFragment(config, 'contact-box')).toEqual(CONTACT_BOX);
    expect(getFragment(config, 'nope')).toBeNull();
    expect(getFragment(config, undefined)).toBeNull();
  });

  it('rejects incomplete records', () => {
    expect(() =>
      registerFragment(config, { id: 'x', title: 'X' } as any),
    ).toThrow(/id, title and html/);
  });

  it('accepts raw registerUtility registrations (the bare convention)', () => {
    (config as any).registerUtility({
      type: FRAGMENT_UTILITY_TYPE,
      name: 'contact-box',
      method: CONTACT_BOX,
    });
    expect(getFragment(config, 'contact-box')).toEqual(CONTACT_BOX);
  });

  it('lists fragments sorted by title, skipping malformed records', () => {
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
  it('passes markup through verbatim without variables', () => {
    const record = { id: 'x', title: 'X', html: '<div class="a">&amp; ok</div>' };
    expect(renderFragmentHtml(record)).toBe('<div class="a">&amp; ok</div>');
  });

  it('substitutes ${var} tokens HTML-escaped, missing ones as empty', () => {
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
  it('view renders the fragment markup as-is', () => {
    registerFragment(config, CONTACT_BOX);
    const out = renderToStaticMarkup(
      <FragmentBlockView data={{ fragment: 'contact-box', variables: { phone: '030' } }} />,
    );
    expect(out).toContain('class="block-fragment"');
    expect(out).toContain('<aside class="contact-box"><h2>Contact</h2><p>030</p></aside>');
  });

  it('view fails soft to the invisible placeholder', () => {
    const out = renderToStaticMarkup(
      <FragmentBlockView data={{ fragment: 'gone' }} />,
    );
    expect(out).toBe('<div class="block-fragment block-fragment-unresolved"></div>');
  });

  it('edit shows honest placeholders for unchosen and unregistered', () => {
    const empty = renderToStaticMarkup(
      <FragmentBlockEdit data={{}} block="b" selected={false} setBlock={() => {}} />,
    );
    expect(empty).toContain('Choose a fragment');
    const gone = renderToStaticMarkup(
      <FragmentBlockEdit data={{ fragment: 'gone' }} block="b" selected={false} setBlock={() => {}} />,
    );
    expect(gone).toContain('not registered');
  });

  it('install registers the block and its schema enumerates fragments', () => {
    registerFragment(config, CONTACT_BOX);
    install(config);
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
