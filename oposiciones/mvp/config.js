/*
 * Tesón MVP · configuración
 * Rellena supabaseUrl y supabaseAnonKey con los datos del proyecto de Supabase
 * (Settings → API). Sin ellos la app funciona igual, pero no envía datos.
 * La anon key es pública por diseño: la tabla solo admite inserciones (ver schema.sql).
 */
window.TESON_CONFIG = {
  supabaseUrl: "",
  supabaseAnonKey: "",
  contactEmail: "hola@tesonopos.es",
  reportResponseHours: 72,
  legal: {
    updated: "",
    controllerName: "",
    taxId: "",
    address: "",
    registryDetails: "",
    processors: "Supabase, Inc. (base de datos y acceso, UE); Postmark (envío de códigos de acceso); Anthropic (preparación del plan, sin datos identificativos); Cloudflare o Netlify (alojamiento web)"
  },
  // Only for the claude.ai preview: fake sign-in (code 123456), no emails sent. Keep false in production.
  demoAuth: false
};
