import { defineConfig } from "vitest/config";
import path from "path";

// Use esbuild's built-in automatic JSX transform (no @vitejs/plugin-react —
// we don't need Fast Refresh for `vitest run`). This emits the react/jsx-runtime
// import, so test/component files need no explicit React import.
export default defineConfig({
  esbuild: { jsx: "automatic", jsxImportSource: "react" },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    css: false,
    include: ["src/**/*.test.{ts,tsx}"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
});
