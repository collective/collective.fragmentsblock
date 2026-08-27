import path from 'node:path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  esbuild: { jsx: 'automatic' },
  resolve: {
    // The promised facade modules exist only in a running host; tests run
    // against minimal stubs with the same surface.
    alias: {
      '@plone/registry': path.resolve(
        import.meta.dirname,
        'test/stubs/plone-registry.ts',
      ),
      '@plone/helpers': path.resolve(
        import.meta.dirname,
        'test/stubs/plone-helpers.ts',
      ),
    },
  },
  test: { environment: 'node' },
});
