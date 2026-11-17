import type { APIRoute } from "astro";
import { indexable, site } from "../site";

export const GET: APIRoute = () => {
  const body = indexable
    ? `User-agent: *\nAllow: /\n\nSitemap: ${site.url}/sitemap-index.xml\n`
    : `# Pre-launch: legal details pending, nothing should be indexed yet.\nUser-agent: *\nDisallow: /\n`;
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
