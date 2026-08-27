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
      dangerouslySetInnerHTML={{
        __html: renderFragmentHtml(record, data.variables),
      }}
    />
  );
};

export default FragmentBlockView;
