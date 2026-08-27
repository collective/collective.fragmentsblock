// Test stub for the @plone/registry facade: the mutable config singleton,
// with the utility registry mirroring @plone/registry's semantics — keyed
// type -> name, entries stored as {method}, getUtilities dropping names.
const utilities: Record<string, Record<string, { method: unknown }>> = {};

const config: any = {
  blocks: { blocksConfig: {} },
  _utilities: utilities,
  registerUtility({ type, name, method }: any) {
    if (!method) throw new Error('No method provided');
    (utilities[type] ??= {})[name] = { method };
  },
  getUtility({ type, name }: any) {
    return utilities[type]?.[name] || {};
  },
  getUtilities({ type }: any) {
    return Object.values(utilities[type] || {});
  },
};

export default config;
