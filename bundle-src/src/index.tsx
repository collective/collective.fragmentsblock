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
  registerFragment,
  getFragment,
  listFragments,
  renderFragmentHtml,
} from './fragments';
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
// install function that registers the block and returns the config.
export default function install(config: any) {
  config.blocks.blocksConfig.fragment = FragmentBlockInfo;
  return config;
}
