/*
 * Tesón website · central settings.
 *
 * `launch.public` stays false until the legal owner details below are filled in.
 * While it is false every page carries `noindex` and robots.txt blocks crawlers,
 * so the site can be live on the domain without appearing in Google.
 * Setting it to true with any legal field empty makes the build fail on purpose.
 */
export const site = {
  name: "Tesón",
  tagline: "Oposiciones, pregunta a pregunta",
  url: "https://tesonopos.es",
  contactEmail: "hola@tesonopos.es",
  // Public address of the practice app. Empty = the app is still in private beta,
  // so the CTAs lead to /beta/ (request a place by email) instead of the app.
  appUrl: "",
  reportResponseHours: 72,
  launch: {
    public: false,
  },
  legal: {
    updated: "",          // e.g. "17 de noviembre de 2026"
    ownerName: "",        // natural person (autónomo) or company name
    taxId: "",            // NIF / NIE / CIF
    address: "",          // full postal address
    registryDetails: "",  // only for a company: Registro Mercantil data
  },
} as const;

export const legalMissing = (["updated", "ownerName", "taxId", "address"] as const).filter(
  (k) => !site.legal[k].trim(),
);
export const legalComplete = legalMissing.length === 0;
export const indexable = site.launch.public && legalComplete;

if (site.launch.public && !legalComplete) {
  throw new Error(
    `launch.public is true but legal fields are missing: ${legalMissing.join(", ")}. ` +
      "Fill them in src/site.ts or set launch.public back to false.",
  );
}

export const ctaHref = site.appUrl || "/beta/";
export const ctaLabel = site.appUrl ? "Practicar gratis" : "Pedir plaza en la beta";
