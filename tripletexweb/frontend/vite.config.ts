import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import checker from "vite-plugin-checker";

export default defineConfig({
  plugins: [
    react(),
  ],
  define: {
    BACKEND_URL_RAW: JSON.stringify(process.env.BACKEND_URL || ''),
  },
  /*build: {
      outDir: path.resolve(__dirname, "build"),
    },*/
  /*
    server: {
      host: "127.0.0.1",
      port: 3000,
    },
    */
});
