import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./", // needed so the packaged Electron app can load assets from disk
  server: {
    host: "127.0.0.1",
    port: 5174,
    strictPort: true,
  },
});