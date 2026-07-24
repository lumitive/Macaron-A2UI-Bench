import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
      },
    },
  },
  server: {
    port: 5174,
    strictPort: true,
    host: "127.0.0.1",
    fs: {
      allow: [
        resolve(__dirname, "."),
        resolve(__dirname, "vendor/a2ui/renderers"),
      ],
    },
  },
});
