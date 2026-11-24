import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    react(),
  ],
  define: {
    BACKEND_URL_RAW: JSON.stringify(process.env.BACKEND_URL || ''),
  },
  // To support running under subpath.
  base: '',
  server: {
    port: 3000,
  },
});
