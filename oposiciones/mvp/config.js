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
  // Only for the claude.ai preview: fake sign-in (code 123456), no emails sent. Keep false in production.
  demoAuth: false
};
