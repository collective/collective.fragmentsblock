// Test stub for the @plone/helpers facade.
import config from './plone-registry';

export const PLONE_BLOCK_TYPE = 'ploneBlock';

// Mirrors @plone/helpers' implementation: the style-field definitions a
// host registers are a `styleFieldDefinition` utility named after the
// field, whose method is a factory returning the definition list.
export const getStyleFieldDefinitionsFromRegistry = (
  fieldName: string,
  args?: unknown,
) => {
  const utility = config.getUtility({
    type: 'styleFieldDefinition',
    name: fieldName,
  });
  return (utility.method as ((args?: unknown) => unknown[]) | undefined)?.(
    args,
  ) ?? [];
};
