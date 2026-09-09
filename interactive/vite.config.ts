/// <reference types="vitest/config" />
import { defineConfig } from "vite";

// The published Jupyter Book serves these assets from a repository subpath
// (https://<user>.github.io/ml-neuro-tutorials/_static/widgets/app/). `base: "./"`
// keeps every generated asset reference relative so the same build works at the
// site root and beneath the project subpath without rewriting.
export default defineConfig({
  base: "./",
  build: {
    // Generated output. Kept out of Git (see repo .gitignore) and reproduced by
    // `npm run build`. Copied through verbatim by Sphinx from book/_static/.
    outDir: "../book/_static/widgets/app",
    emptyOutDir: true,
    target: "es2020",
    sourcemap: false,
  },
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
});
