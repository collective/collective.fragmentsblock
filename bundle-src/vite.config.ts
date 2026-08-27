// The canonical block add-on library build (block add-on contract §1.2):
// ESM lib, automatic JSX runtime, every promised shared module external
// (resolved in the browser via the @@aurora-edit import map to the host's
// facades), CSS scope-wrapped in the same build. Output is committed into
// the Python package's static/ (ADR 0010 style) — Node is a packaging-time
// tool only.
import path from 'node:path';
import { defineConfig, type Plugin } from 'vite';
import { scopeWrap } from './build-plugins/scope-wrap';

// The promised singleton-critical modules (contract §2.1). Anything else
// the bundle must carry itself.
const SHARED_MODULES = [
  'react',
  'react/jsx-runtime',
  'react-dom',
  'react-dom/client',
  'jotai',
  'platejs',
  '@plone/registry',
  '@plone/helpers',
];

// A promised module leaking into the bundle means two Reacts at runtime
// (null hook dispatcher) — fail the build instead (contract §1.2).
function assertNoSharedInBundle(): Plugin {
  const banned =
    /\/node_modules\/(?:\.pnpm\/[^/]+\/node_modules\/)?(react|react-dom|jotai|platejs|@plone\/registry|@plone\/helpers)\//;
  return {
    name: 'assert-no-shared-in-bundle',
    generateBundle() {
      for (const id of this.getModuleIds()) {
        if (banned.test(id)) {
          throw new Error(
            `Promised shared module bundled: ${id} — it must stay external ` +
              '(block add-on contract §2.1).',
          );
        }
      }
    },
  };
}

export default defineConfig({
  // Lib mode defaults to the classic JSX transform, which crashes at render
  // time on the missing global React; the automatic runtime resolves
  // react/jsx-runtime through the import map instead.
  esbuild: { jsx: 'automatic' },
  plugins: [
    {
      // enforce post: in a lib build Vite's internal css-post plugin emits
      // the CSS asset late in generateBundle; the wrap must run after it.
      ...scopeWrap({
        // The editor's roots plus the public blocks-view root (contract
        // §6.1): one asset styles both surfaces via anatomy-class parity.
        scopeRoots: [
          '.aurora-editor',
          '.aurora-editor-portal',
          '.aurora-blocks-view',
        ],
        scopeLimit: '.aurora-pattern-island',
      }),
      enforce: 'post',
    },
    assertNoSharedInBundle(),
  ],
  build: {
    lib: {
      entry: path.resolve(import.meta.dirname, 'src/index.tsx'),
      formats: ['es'],
      fileName: () => 'fragment-block.js',
    },
    outDir: path.resolve(
      import.meta.dirname,
      '../src/collective/fragmentsblock/static',
    ),
    emptyOutDir: false,
    target: 'es2022',
    minify: false,
    sourcemap: true,
    rollupOptions: {
      external: SHARED_MODULES,
      output: {
        assetFileNames: 'fragment-block.[ext]',
      },
    },
  },
});
