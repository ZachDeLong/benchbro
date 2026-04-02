import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../src/benchbro/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://localhost:7853",
      "/ws": { target: "ws://localhost:7853", ws: true },
    },
  },
});
