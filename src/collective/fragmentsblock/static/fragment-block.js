import { jsx, jsxs } from "react/jsx-runtime";
import config from "@plone/registry";
import { getStyleFieldDefinitionsFromRegistry } from "@plone/helpers";
const FRAGMENT_UTILITY_TYPE = "collective.fragmentsblock.fragment";
const FRAGMENT_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;
function registerFragment(config2, record) {
  if (!record?.id || !record.title || typeof record.html !== "string") {
    throw new Error(
      "registerFragment: a fragment record needs id, title and html"
    );
  }
  if (!FRAGMENT_ID_RE.test(record.id)) {
    throw new Error(
      `registerFragment: ${JSON.stringify(record.id)} is not a valid fragment id (must match /^[A-Za-z0-9][A-Za-z0-9_-]*$/, because the server resolves it to a filename)`
    );
  }
  config2.registerUtility({
    type: FRAGMENT_UTILITY_TYPE,
    name: record.id,
    method: record
  });
}
function asRecord(utility) {
  const record = utility?.method;
  if (!record || typeof record.html !== "string" || !record.title) return null;
  if (typeof record.id !== "string" || !FRAGMENT_ID_RE.test(record.id)) {
    console.warn(
      "collective.fragmentsblock: ignoring a fragment record with an invalid id:",
      record?.id
    );
    return null;
  }
  return record;
}
function getFragment(config2, id) {
  if (typeof id !== "string" || !id) return null;
  return asRecord(config2.getUtility({ type: FRAGMENT_UTILITY_TYPE, name: id }));
}
function listFragments(config2) {
  return config2.getUtilities({ type: FRAGMENT_UTILITY_TYPE }).map(asRecord).filter((record) => record !== null).sort((a, b) => a.title.localeCompare(b.title));
}
const TOKEN = /\$\{([A-Za-z_][A-Za-z0-9_]*)\}/g;
function escapeHtml(value) {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
}
function coerce(value) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "";
  return "";
}
function renderFragmentHtml(record, variables) {
  const values = variables && typeof variables === "object" ? variables : {};
  return record.html.replace(
    TOKEN,
    (_match, name) => (
      // hasOwn, not `values[name]`: a token named like an Object.prototype
      // member (${toString}, ${constructor}) would otherwise resolve to the
      // inherited member here and to nothing on the server.
      Object.hasOwn(values, name) ? escapeHtml(coerce(values[name])) : ""
    )
  );
}
const FragmentBlockView = ({ data }) => {
  const record = getFragment(config, data.fragment);
  if (!record) {
    return /* @__PURE__ */ jsx("div", { className: "block-fragment block-fragment-unresolved" });
  }
  return /* @__PURE__ */ jsx(
    "div",
    {
      className: "block-fragment",
      dangerouslySetInnerHTML: {
        __html: renderFragmentHtml(record, data.variables)
      }
    }
  );
};
const FragmentBlockEdit = (props) => {
  const { data } = props;
  if (!data.fragment) {
    return /* @__PURE__ */ jsx("div", { className: "block-fragment block-fragment-placeholder", children: /* @__PURE__ */ jsx("p", { className: "fragment-note", children: "Choose a fragment in the block settings." }) });
  }
  if (!getFragment(config, data.fragment)) {
    return /* @__PURE__ */ jsx("div", { className: "block-fragment block-fragment-placeholder", children: /* @__PURE__ */ jsxs("p", { className: "fragment-note", children: [
      "The fragment “",
      String(data.fragment),
      "” is not registered — its add-on may be uninstalled. The published page renders nothing here."
    ] }) });
  }
  return /* @__PURE__ */ jsx(FragmentBlockView, { ...props, isEditMode: true });
};
const FragmentIcon = (props) => /* @__PURE__ */ jsxs(
  "svg",
  {
    xmlns: "http://www.w3.org/2000/svg",
    width: "24",
    height: "24",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    ...props,
    children: [
      /* @__PURE__ */ jsx("rect", { width: "14", height: "14", x: "8", y: "8", rx: "2", ry: "2" }),
      /* @__PURE__ */ jsx("path", { d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" })
    ]
  }
);
const BLOCK_WIDTH_FIELD = {
  title: "Block width",
  widget: "width",
  // The width nodes already render at when they carry none, so adding the
  // control leaves every existing fragment block exactly where it was.
  default: "default",
  styleField: true
};
const BACKGROUND_FIELD_NAME = "backgroundColor";
function backgroundField(data) {
  const definitions = getStyleFieldDefinitionsFromRegistry(
    BACKGROUND_FIELD_NAME,
    // A definition factory MAY vary its palette by block; pass the block's
    // own data so one that does sees this block rather than a blank.
    { data, blockType: "fragment", fieldName: BACKGROUND_FIELD_NAME }
  );
  const choices = definitions.filter((definition) => typeof definition?.name === "string").map((definition) => [definition.name, definition.label || definition.name]);
  if (!choices.length) return null;
  return {
    title: "Background",
    choices,
    // Only the conventional neutral slot may be a default; anything else
    // would paint every fragment block ever inserted. A palette without
    // one gets no default at all — an unresolvable value contributes no
    // style, which is the same "unpainted" the neutral slot means.
    ...choices.some(([name]) => name === "none") ? { default: "none" } : {},
    styleField: true
  };
}
function FragmentSchema(args) {
  const fields = ["fragment", "blockWidth"];
  const properties = {
    fragment: {
      title: "Fragment",
      description: "A registered design fragment, rendered as-is.",
      // The leading empty choice keeps the select honest: a select
      // whose options all name a fragment would show the first one as
      // chosen while the block still stores nothing.
      choices: [
        ["", "— Choose a fragment —"],
        ...listFragments(config).map((record) => [
          record.id,
          record.title
        ])
      ]
    },
    blockWidth: { ...BLOCK_WIDTH_FIELD }
  };
  const background = backgroundField(args?.data ?? {});
  if (background) {
    fields.push(BACKGROUND_FIELD_NAME);
    properties[BACKGROUND_FIELD_NAME] = background;
  }
  return {
    title: "Fragment",
    fieldsets: [
      {
        id: "default",
        title: "Default",
        fields
      }
    ],
    properties,
    required: ["fragment"]
  };
}
const FragmentBlockInfo = {
  id: "fragment",
  title: "Fragment",
  edit: FragmentBlockEdit,
  view: FragmentBlockView,
  blockSchema: FragmentSchema,
  icon: FragmentIcon,
  category: "fragment"
};
function install(config2) {
  config2.blocks.blocksConfig.fragment = FragmentBlockInfo;
  return config2;
}
export {
  FRAGMENT_UTILITY_TYPE,
  install as default,
  getFragment,
  listFragments,
  registerFragment,
  renderFragmentHtml
};
//# sourceMappingURL=fragment-block.js.map
