import config from '@plone/registry';
import type { BlockViewProps } from './types';
import { getFragment, renderFragmentHtml } from './fragments';

// Renders the registered fragment's markup as-is (after ${var}
// substitution from the block's persisted `variables` mapping). Everything
// is client-side registry data — no server round-trip, no derived fields.
// Fail-soft: an id whose provider is gone renders the same invisible
// placeholder as the server renderer.
const FragmentBlockView = ({ data }: BlockViewProps) => {
  const record = getFragment(config as any, data.fragment);
  if (!record) {
    return <div className="block-fragment block-fragment-unresolved" />;
  }
  return (
    <div
      className="block-fragment"
      // The fragment's title is the ONLY thing that tells two fragment blocks
      // apart: the block's own label is the constant "Fragment", and a
      // fragment is often decoration with no text to read (an `aria-hidden`
      // divider). `data-block-summary` is the editor's hook for exactly that
      // — the drag rows name a block by it (block add-on contract §1.6) — and
      // it is inert everywhere else, including on the classic page, whose
      // server-rendered markup does not carry it.
      data-block-summary={record.title}
      dangerouslySetInnerHTML={{
        __html: renderFragmentHtml(record, data.variables),
      }}
    />
  );
};

export default FragmentBlockView;
