import config from '@plone/registry';
import { listFragments } from './fragments';

// blockSchema may be a function; Aurora consumes it lazily when building
// the sidebar form (contract §1.3), i.e. after every add-on's install has
// registered its fragments — so the choices enumerate the full registry.
export function FragmentSchema() {
  return {
    title: 'Fragment',
    fieldsets: [
      {
        id: 'default',
        title: 'Default',
        fields: ['fragment'],
      },
    ],
    properties: {
      fragment: {
        title: 'Fragment',
        description: 'A registered design fragment, rendered as-is.',
        // The leading empty choice keeps the select honest: a select
        // whose options all name a fragment would show the first one as
        // chosen while the block still stores nothing.
        choices: [
          ['', '— Choose a fragment —'],
          ...listFragments(config as any).map((record) => [
            record.id,
            record.title,
          ]),
        ],
      },
    },
    required: ['fragment'],
  };
}
