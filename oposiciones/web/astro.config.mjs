import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://tesonopos.es",
  trailingSlash: "always",
  build: { format: "directory", inlineStylesheets: "never" },
  integrations: [sitemap({ filter: (page) => !page.includes("/404") })],
});
