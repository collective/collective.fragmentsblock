// Local structural types for the Aurora adapter contract (block add-on
// contract §1) — deliberately loose, so the package needs no dependency on
// @plone/types.
export type BlockData = Record<string, any>;

export type BlockViewProps = {
  data: BlockData;
  isEditMode?: boolean;
};

export type BlockEditProps = {
  data: BlockData;
  block: string;
  selected: boolean;
  setBlock: (data: BlockData) => void;
  [key: string]: any;
};
