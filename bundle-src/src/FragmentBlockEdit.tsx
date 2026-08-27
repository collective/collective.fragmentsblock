import config from '@plone/registry';
import type { BlockEditProps } from './types';
import FragmentBlockView from './FragmentBlockView';
import { getFragment } from './fragments';

// The picker itself is the sidebar's schema-driven Choice field; the edit
// surface only mirrors the public rendering, plus honest placeholders for
// the two editor-facing gaps the public page hides (nothing chosen yet, or
// the chosen fragment's provider is no longer installed).
const FragmentBlockEdit = (props: BlockEditProps) => {
  const { data } = props;
  if (!data.fragment) {
    return (
      <div className="block-fragment block-fragment-placeholder">
        <p className="fragment-note">
          Choose a fragment in the block settings.
        </p>
      </div>
    );
  }
  if (!getFragment(config as any, data.fragment)) {
    return (
      <div className="block-fragment block-fragment-placeholder">
        <p className="fragment-note">
          The fragment “{String(data.fragment)}” is not registered — its
          add-on may be uninstalled. The published page renders nothing
          here.
        </p>
      </div>
    );
  }
  return <FragmentBlockView {...props} isEditMode />;
};

export default FragmentBlockEdit;
