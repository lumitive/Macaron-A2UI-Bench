import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        showcase: resolve(__dirname, "showcase.html"),
      },
    },
  },
  server: {
    port: 5180,
    strictPort: true,
    fs: {
      allow: [
        resolve(__dirname, "."),
        resolve(__dirname, "vendor/a2ui/renderers"),
      ],
    },
  },
});
