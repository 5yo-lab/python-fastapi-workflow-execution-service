import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/workflows": "http://localhost:8000",
      "/actions": "http://localhost:8000",
    },
  },
});
