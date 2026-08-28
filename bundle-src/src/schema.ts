import config from '@plone/registry';
import { getStyleFieldDefinitionsFromRegistry } from '@plone/helpers';
import { listFragments } from './fragments';

// Aurora *style fields*: a schema property marked `styleField: true` is
// resolved by StyleFieldsKit into inline CSS custom properties plus a
// `has--<field>--<value>` class on the block wrapper, and the classic
// renderer stamps the same pair while walking the tree. Both live entirely
// outside this block — the fragment's own markup and both view components
// stay untouched; declaring the field is the whole of the wiring.
//
// `blockWidth` is the width field every host block carries (contract §1.4:
// the field is what hands the author the control; a block that wants a
// fixed width omits it and declares `defaultBlockWidth` instead). A
// fragment is a piece of a design, not a design, so its placement — a
// full-bleed divider, a narrow contact box — belongs to the page it sits
// on, not to the file.
const BLOCK_WIDTH_FIELD = {
  title: 'Block width',
  widget: 'width',
  // The width nodes already render at when they carry none, so adding the
  // control leaves every existing fragment block exactly where it was.
  default: 'default',
  styleField: true,
};

// Backgrounds are the host's palette, not ours: the author picks a *named*
// slot and the theme owns what it looks like. Reading the definitions the
// host registered (rather than hardcoding a list) is also the only honest
// option — an unknown value resolves to no style, so a slot this block
// invented would render as nothing.
const BACKGROUND_FIELD_NAME = 'backgroundColor';

function backgroundField(data: Record<string, unknown>) {
  const definitions = getStyleFieldDefinitionsFromRegistry(
    BACKGROUND_FIELD_NAME,
    // A definition factory MAY vary its palette by block; pass the block's
    // own data so one that does sees this block rather than a blank.
    { data, blockType: 'fragment', fieldName: BACKGROUND_FIELD_NAME },
  );
  const choices = definitions
    .filter((definition) => typeof definition?.name === 'string')
    .map((definition) => [definition.name, definition.label || definition.name]);
  // A host that registers no palette (Aurora proper today) gets no field
  // rather than a select whose every option resolves to nothing.
  if (!choices.length) return null;
  return {
    title: 'Background',
    choices,
    // Only the conventional neutral slot may be a default; anything else
    // would paint every fragment block ever inserted. A palette without
    // one gets no default at all — an unresolvable value contributes no
    // style, which is the same "unpainted" the neutral slot means.
    ...(choices.some(([name]) => name === 'none') ? { default: 'none' } : {}),
    styleField: true,
  };
}

// blockSchema may be a function; Aurora consumes it lazily when building
// the sidebar form (contract §1.3), i.e. after every add-on's install has
// registered its fragments — so the choices enumerate the full registry.
// The background palette is read on the same lazy path, and for the same
// reason: the host registers its definitions during bootstrap.
export function FragmentSchema(args?: { data?: Record<string, unknown> }) {
  const fields = ['fragment', 'blockWidth'];
  const properties: Record<string, unknown> = {
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
    blockWidth: { ...BLOCK_WIDTH_FIELD },
  };

  const background = backgroundField(args?.data ?? {});
  if (background) {
    fields.push(BACKGROUND_FIELD_NAME);
    properties[BACKGROUND_FIELD_NAME] = background;
  }

  return {
    title: 'Fragment',
    fieldsets: [
      {
        id: 'default',
        title: 'Default',
        fields,
      },
    ],
    properties,
    required: ['fragment'],
  };
}
