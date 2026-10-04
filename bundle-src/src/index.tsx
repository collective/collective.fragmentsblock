import FragmentBlockEdit from './FragmentBlockEdit';
import FragmentBlockView from './FragmentBlockView';
import FragmentIcon from './FragmentIcon';
import { FragmentSchema } from './schema';
import './styles.css';

// The fragment registration API for provider add-ons. Providers may also
// skip this package entirely and call config.registerUtility with
// FRAGMENT_UTILITY_TYPE directly — the registry is the contract, these are
// conveniences around it.
export {
  FRAGMENT_UTILITY_TYPE,
  FRAGMENTS_SERVICE,
  registerFragment,
  getFragment,
  listFragments,
  loadFragments,
  getFragmentsLoadError,
  renderFragmentHtml,
} from './fragments';
import { loadFragments, setFragmentsLoadError } from './fragments';
export type { FragmentRecord } from './fragments';

const FragmentBlockInfo = {
  id: 'fragment',
  title: 'Fragment',
  edit: FragmentBlockEdit,
  view: FragmentBlockView,
  blockSchema: FragmentSchema,
  icon: FragmentIcon,
  category: 'fragment',
};

// The loader convention (block add-on contract §1): default-export an
// install function that registers the block and returns the config. It is
// async, and the host awaits it (block-api 1.2), because the fragments come
// from the server: `@fragments` lists every provider's records, and they
// have to be in the registry before the first render (ADR 0002). A failed
// load keeps the block — the picker is empty and existing fragment blocks
// say why — rather than losing the whole block to the host's fail-soft skip.
export default async function install(config: any) {
  config.blocks.blocksConfig.fragment = FragmentBlockInfo;
  try {
    await loadFragments(config);
    setFragmentsLoadError(null);
  } catch (error) {
    console.warn(
      'collective.fragmentsblock: the fragment list could not be loaded; ' +
        'the picker stays empty:',
      error,
    );
    setFragmentsLoadError(error);
  }
  return config;
}
