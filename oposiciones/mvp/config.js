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
    processors: "Supabase, Inc. (alojamiento de datos en la Unión Europea)"
  }
};
