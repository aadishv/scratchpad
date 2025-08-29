import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { URL, fileURLToPath } from "url";
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate", // Automatically update the PWA
      includeAssets: [
        'favicon.png', // or your favicon's full name
        'Geist-P*.woff2', // Using a glob pattern for fonts
        'GeistM*.woff2',
        'pp-edit*.woff2'
      ],
      manifest: {
        name: "Dotlist Lite",
        short_name: "Dotlist",
        description: "Dotlist Lite is a simple, fast, and polished task management app.",
        theme_color: "#ffffff",
        icons: [
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },
    }),
  ],
  resolve: {
      alias: {
        // Update this alias
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
});
