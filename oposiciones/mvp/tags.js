/*
 * Tesón · etiquetas de aprendizaje (v1)
 * Áreas → conceptos → preguntas; confusiones típicas por opción incorrecta;
 * dificultad inicial; formularios de control para el experimento.
 * Se aplica sobre window.TESON_BANK (questions.js).
 */
(function () {
  var B = window.TESON_BANK;

  // Áreas del tema (lo que ve el opositor en «Tu Constitución»).
  B.areas = {
    EST: "Estructura y elaboración",
    TP: "Título Preliminar",
    DF: "Derechos fundamentales",
    DC: "Derechos, deberes y principios rectores",
    GS: "Garantías y suspensión",
    CO: "La Corona",
    CG: "Cortes Generales",
    GA: "Gobierno y Administración",
    PJ: "Poder Judicial",
    EH: "Economía y Hacienda",
    OT: "Organización territorial",
    TC: "Tribunal Constitucional",
    REF: "Reforma constitucional"
  };

  // Conceptos: unidad mínima de seguimiento. imp = importancia en el examen (1–3).
  // OJO: imp es una ESTIMACIÓN inicial. Sustituir por la frecuencia real en los exámenes
  // oficiales del INAP cuando llegue la investigación (brief, Parte A).
  B.concepts = {
    "est.estructura": { imp: 2, area: "EST", name: "Estructura de la Constitución", arts: "Títulos y artículos" },
    "est.fechas": { imp: 2, area: "EST", name: "Aprobación, referéndum y entrada en vigor", arts: "Disp. final" },
    "est.reformas": { imp: 2, area: "EST", name: "Reformas realizadas", arts: "13.2, 135, 49" },
    "tp.valores": { imp: 3, area: "TP", name: "Estado social y valores superiores", arts: "1.1" },
    "tp.soberania": { imp: 3, area: "TP", name: "Soberanía y forma política", arts: "1.2–1.3" },
    "tp.autonomia": { imp: 2, area: "TP", name: "Unidad y autonomía", arts: "2" },
    "tp.lenguas": { imp: 2, area: "TP", name: "Lenguas oficiales", arts: "3" },
    "tp.simbolos": { imp: 1, area: "TP", name: "Bandera y capital", arts: "4–5" },
    "tp.partidos": { imp: 2, area: "TP", name: "Partidos, sindicatos y asociaciones empresariales", arts: "6–7" },
    "tp.ffaa": { imp: 1, area: "TP", name: "Fuerzas Armadas", arts: "8" },
    "tp.art9": { imp: 3, area: "TP", name: "Sujeción a la Constitución y principios del art. 9", arts: "9" },
    "df.nacionalidad": { imp: 2, area: "DF", name: "Interpretación, nacionalidad y mayoría de edad", arts: "10–12" },
    "df.extranjeros": { imp: 2, area: "DF", name: "Extranjeros y extradición", arts: "13" },
    "df.igualdad": { imp: 3, area: "DF", name: "Igualdad ante la ley", arts: "14" },
    "df.vida_religion": { imp: 2, area: "DF", name: "Vida y libertad ideológica y religiosa", arts: "15–16" },
    "df.detencion": { imp: 3, area: "DF", name: "Libertad y detención", arts: "17" },
    "df.intimidad": { imp: 2, area: "DF", name: "Intimidad, domicilio y comunicaciones", arts: "18" },
    "df.expresion": { imp: 2, area: "DF", name: "Libertades de expresión e información", arts: "20" },
    "df.reunion": { imp: 2, area: "DF", name: "Reunión y asociación", arts: "21–22" },
    "df.participacion": { imp: 3, area: "DF", name: "Participación y tutela judicial", arts: "23–24" },
    "df.legalidad": { imp: 2, area: "DF", name: "Legalidad sancionadora y Tribunales de Honor", arts: "25–26" },
    "df.educacion": { imp: 2, area: "DF", name: "Educación, sindicación, huelga y petición", arts: "27–29" },
    "df.titulo1": { imp: 3, area: "DF", name: "Estructura del Título I", arts: "Caps. I–V" },
    "dc.deberes": { imp: 2, area: "DC", name: "Derechos y deberes de los ciudadanos", arts: "30–38" },
    "dc.rectores": { imp: 2, area: "DC", name: "Principios rectores", arts: "39–52" },
    "gs.tutela": { imp: 3, area: "GS", name: "Tutela de los derechos y amparo", arts: "53" },
    "gs.defensor": { imp: 2, area: "GS", name: "Defensor del Pueblo", arts: "54" },
    "gs.suspension": { imp: 3, area: "GS", name: "Suspensión de derechos", arts: "55" },
    "gs.estados": { imp: 3, area: "GS", name: "Estados de alarma, excepción y sitio", arts: "116" },
    "ref.iniciativa": { imp: 2, area: "REF", name: "Iniciativa de reforma", arts: "166" },
    "ref.ordinaria": { imp: 3, area: "REF", name: "Procedimiento ordinario", arts: "167" },
    "ref.agravada": { imp: 3, area: "REF", name: "Procedimiento agravado", arts: "168" },
    "ref.limites": { imp: 2, area: "REF", name: "Límites temporales a la reforma", arts: "169" },
    // Títulos II–IX: de momento solo con preguntas oficiales del INAP (oficiales.js).
    "co.funciones": { imp: 3, area: "CO", name: "Funciones del Rey", arts: "56, 62–63" },
    "co.sucesion": { imp: 2, area: "CO", name: "Sucesión a la Corona", arts: "57" },
    "co.regencia": { imp: 2, area: "CO", name: "Consorte, Regencia y tutela", arts: "58–60" },
    "co.refrendo": { imp: 2, area: "CO", name: "Refrendo y Casa del Rey", arts: "64–65" },
    "cg.composicion": { imp: 3, area: "CG", name: "Congreso y Senado: composición y estatuto", arts: "66–71" },
    "cg.funcionamiento": { imp: 3, area: "CG", name: "Funcionamiento de las Cámaras", arts: "72–80" },
    "cg.leyes": { imp: 3, area: "CG", name: "Elaboración de las leyes", arts: "81–92" },
    "cg.tratados": { imp: 2, area: "CG", name: "Tratados internacionales", arts: "93–96" },
    "ga.gobierno": { imp: 3, area: "GA", name: "El Gobierno", arts: "97–102" },
    "ga.relaciones": { imp: 2, area: "GA", name: "Relaciones entre el Gobierno y las Cortes", arts: "108–115" },
    "ga.administracion": { imp: 2, area: "GA", name: "Administración y Consejo de Estado", arts: "103–107" },
    "pj.principios": { imp: 3, area: "PJ", name: "Principios del Poder Judicial", arts: "117–121" },
    "pj.cgpj": { imp: 3, area: "PJ", name: "Consejo General del Poder Judicial", arts: "122" },
    "pj.ts_fiscal": { imp: 2, area: "PJ", name: "Tribunal Supremo y Ministerio Fiscal", arts: "123–127" },
    "eh.hacienda": { imp: 2, area: "EH", name: "Hacienda, presupuestos y deuda", arts: "128–136" },
    "ot.principios": { imp: 2, area: "OT", name: "Principios de la organización territorial", arts: "137–139" },
    "ot.local": { imp: 2, area: "OT", name: "Administración local", arts: "140–142" },
    "ot.estatutos": { imp: 3, area: "OT", name: "Comunidades Autónomas y Estatutos", arts: "143–148" },
    "ot.competencias": { imp: 3, area: "OT", name: "Competencias del Estado y transferencias", arts: "149–151" },
    "ot.control": { imp: 2, area: "OT", name: "Órganos y control de las Comunidades Autónomas", arts: "152–158" },
    "tc.composicion": { imp: 3, area: "TC", name: "Composición del Tribunal Constitucional", arts: "159–160" },
    "tc.competencias": { imp: 3, area: "TC", name: "Competencias y legitimación ante el Tribunal Constitucional", arts: "161–165" }
  };

  // Confusiones típicas (se detectan cuando el opositor elige ciertas opciones incorrectas).
  B.misconceptions = {
    "mis.estados": { name: "Alarma, excepción y sitio", esquema: "estados" },
    "mis.reforma": { name: "Reforma ordinaria (art. 167) y agravada (art. 168)", esquema: "reforma" },
    "mis.art23_103": { name: "Art. 23.2 (igualdad y requisitos legales) y art. 103.3 (mérito y capacidad)", esquema: null },
    "mis.amparo": { name: "Qué derechos tienen amparo y procedimiento preferente", esquema: "titulo1" },
    "mis.literal": { name: "La literalidad exacta del texto (villa/ciudad, deber/derecho…)", esquema: null },
    "mis.partidos": { name: "Partidos políticos (art. 6) y sindicatos (art. 7)", esquema: null },
    "mis.autoriza": { name: "Quién puede autorizar: un juez o la Administración", esquema: "derechos" },
    "mis.suspension": { name: "Qué derechos pueden suspenderse (art. 55)", esquema: "suspension" },
    "mis.rango": { name: "Ley orgánica, ley ordinaria o reglamento", esquema: "leyes" },
    "mis.cifras": { name: "Plazos y cifras (72 horas, 15/30 días, 169 artículos…)", esquema: null },
    "mis.valores": { name: "Valores superiores (art. 1.1) frente a otros principios", esquema: "valores" },
    "mis.ubicacion": { name: "Dónde está cada precepto (capítulos y secciones)", esquema: "titulo1" },
    "mis.quien": { name: "Quién propone y quién nombra (Rey, Gobierno, Cortes, CGPJ…)", esquema: "nombramientos" },
    "mis.mayorias": { name: "Mayorías: simple, absoluta, tres quintos y dos tercios", esquema: "mayorias" }
  };

  // id: [conceptos], dificultad inicial (1–3), confusiones por índice de opción.
  var T = {
    "CE-001": [["est.estructura"], 1, { 0: "mis.cifras", 1: "mis.cifras", 3: "mis.cifras" }],
    "CE-002": [["est.fechas"], 2, { 0: "mis.cifras", 1: "mis.cifras", 3: "mis.cifras" }],
    "CE-003": [["est.estructura"], 1, { 0: "mis.ubicacion", 1: "mis.ubicacion", 2: "mis.ubicacion" }],
    "CE-004": [["est.reformas"], 2, {}],
    "CE-005": [["tp.valores"], 2, { 1: "mis.valores", 2: "mis.valores", 3: "mis.valores" }],
    "CE-006": [["tp.soberania"], 1, {}],
    "CE-007": [["tp.soberania"], 1, { 0: "mis.valores", 2: "mis.literal" }],
    "CE-008": [["tp.autonomia"], 2, { 1: "mis.ubicacion", 2: "mis.ubicacion" }],
    "CE-009": [["tp.lenguas"], 1, { 0: "mis.literal", 2: "mis.literal", 3: "mis.literal" }],
    "CE-010": [["tp.lenguas"], 1, { 1: "mis.rango" }],
    "CE-011": [["tp.simbolos"], 1, { 1: "mis.literal", 2: "mis.literal" }],
    "CE-012": [["tp.simbolos"], 2, { 2: "mis.rango" }],
    "CE-013": [["tp.simbolos"], 2, { 1: "mis.literal", 3: "mis.rango" }],
    "CE-014": [["tp.partidos"], 2, { 0: "mis.literal" }],
    "CE-015": [["tp.partidos"], 1, { 1: "mis.partidos", 3: "mis.ubicacion" }],
    "CE-016": [["tp.partidos"], 2, { 0: "mis.partidos", 1: "mis.partidos", 2: "mis.partidos" }],
    "CE-017": [["tp.ffaa"], 1, {}],
    "CE-018": [["tp.ffaa"], 1, { 0: "mis.rango", 2: "mis.rango", 3: "mis.rango" }],
    "CE-019": [["tp.art9"], 1, {}],
    "CE-020": [["tp.art9"], 3, { 0: "mis.valores", 1: "mis.valores", 2: "mis.valores" }],
    "CE-021": [["tp.art9"], 2, {}],
    "CE-022": [["tp.art9"], 2, { 1: "mis.literal", 2: "mis.literal", 3: "mis.literal" }],
    "CE-023": [["df.nacionalidad"], 2, {}],
    "CE-024": [["df.nacionalidad"], 1, { 1: "mis.cifras", 2: "mis.cifras", 3: "mis.rango" }],
    "CE-025": [["df.nacionalidad"], 2, { 0: "mis.literal" }],
    "CE-026": [["df.extranjeros"], 2, {}],
    "CE-027": [["df.extranjeros"], 1, {}],
    "CE-028": [["df.igualdad", "df.titulo1"], 3, { 0: "mis.ubicacion", 1: "mis.ubicacion", 3: "mis.ubicacion" }],
    "CE-029": [["df.igualdad"], 2, {}],
    "CE-030": [["df.vida_religion"], 2, { 0: "mis.literal" }],
    "CE-031": [["df.vida_religion"], 1, { 3: "mis.rango" }],
    "CE-032": [["df.vida_religion"], 1, {}],
    "CE-033": [["df.detencion"], 1, { 0: "mis.cifras", 1: "mis.cifras", 3: "mis.cifras" }],
    "CE-034": [["df.detencion"], 2, { 0: "mis.amparo" }],
    "CE-035": [["df.detencion"], 1, {}],
    "CE-036": [["df.intimidad"], 2, { 0: "mis.autoriza", 1: "mis.autoriza", 3: "mis.autoriza" }],
    "CE-037": [["df.intimidad"], 2, { 0: "mis.autoriza", 1: "mis.suspension" }],
    "CE-038": [["df.intimidad"], 2, { 1: "mis.ubicacion", 2: "mis.ubicacion", 3: "mis.ubicacion" }],
    "CE-039": [["df.expresion"], 3, { 0: "mis.autoriza", 2: "mis.rango", 3: "mis.suspension" }],
    "CE-040": [["df.expresion"], 1, { 0: "mis.autoriza", 1: "mis.autoriza", 3: "mis.autoriza" }],
    "CE-041": [["df.expresion"], 2, { 1: "mis.ubicacion", 2: "mis.ubicacion", 3: "mis.ubicacion" }],
    "CE-042": [["df.reunion"], 1, { 0: "mis.autoriza", 1: "mis.literal" }],
    "CE-043": [["df.reunion"], 2, { 3: "mis.literal" }],
    "CE-044": [["df.reunion"], 1, { 1: "mis.autoriza", 2: "mis.autoriza", 3: "mis.autoriza" }],
    "CE-045": [["df.reunion"], 1, {}],
    "CE-046": [["df.reunion"], 2, {}],
    "CE-047": [["df.participacion"], 3, { 0: "mis.art23_103" }],
    "CE-048": [["df.participacion"], 2, {}],
    "CE-049": [["df.legalidad"], 2, { 2: "mis.autoriza", 3: "mis.suspension" }],
    "CE-050": [["df.legalidad"], 2, { 3: "mis.literal" }],
    "CE-051": [["df.educacion"], 1, { 3: "mis.cifras" }],
    "CE-052": [["df.educacion"], 3, { 3: "mis.literal" }],
    "CE-053": [["df.educacion"], 1, { 1: "mis.cifras" }],
    "CE-054": [["df.educacion"], 2, {}],
    "CE-055": [["df.titulo1"], 2, { 0: "mis.ubicacion", 2: "mis.ubicacion", 3: "mis.ubicacion" }],
    "CE-056": [["gs.tutela", "dc.deberes"], 3, { 0: "mis.amparo", 1: "mis.amparo", 3: "mis.amparo" }],
    "CE-057": [["dc.deberes"], 1, {}],
    "CE-058": [["dc.deberes"], 1, { 0: "mis.ubicacion", 2: "mis.ubicacion", 3: "mis.ubicacion" }],
    "CE-059": [["dc.deberes"], 2, {}],
    "CE-060": [["dc.deberes"], 1, { 0: "mis.ubicacion" }],
    "CE-061": [["dc.deberes"], 2, { 1: "mis.literal" }],
    "CE-062": [["dc.rectores", "gs.tutela"], 2, { 0: "mis.amparo", 2: "mis.amparo" }],
    "CE-063": [["dc.rectores"], 1, { 0: "mis.ubicacion", 1: "mis.ubicacion", 2: "mis.ubicacion" }],
    "CE-064": [["dc.rectores", "est.reformas"], 1, { 1: "mis.literal" }],
    "CE-065": [["dc.rectores", "df.titulo1"], 2, { 0: "mis.ubicacion", 1: "mis.ubicacion", 3: "mis.ubicacion" }],
    "CE-066": [["gs.tutela"], 2, { 1: "mis.amparo", 2: "mis.amparo", 3: "mis.amparo" }],
    "CE-067": [["gs.tutela"], 1, {}],
    "CE-068": [["gs.tutela"], 2, {}],
    "CE-069": [["gs.defensor"], 1, {}],
    "CE-070": [["gs.defensor"], 1, { 0: "mis.rango", 1: "mis.rango", 3: "mis.rango" }],
    "CE-071": [["gs.suspension"], 3, { 0: "mis.suspension", 1: "mis.suspension", 3: "mis.suspension" }],
    "CE-072": [["gs.suspension"], 3, { 0: "mis.suspension", 1: "mis.suspension", 2: "mis.suspension" }],
    "CE-073": [["gs.suspension"], 2, {}],
    "CE-074": [["gs.estados"], 2, { 1: "mis.estados", 2: "mis.estados" }],
    "CE-075": [["gs.estados"], 2, { 0: "mis.estados", 2: "mis.cifras", 3: "mis.cifras" }],
    "CE-076": [["gs.estados"], 2, { 0: "mis.estados", 1: "mis.estados", 2: "mis.cifras" }],
    "CE-077": [["ref.iniciativa"], 1, {}],
    "CE-078": [["ref.ordinaria"], 2, { 1: "mis.reforma", 2: "mis.cifras", 3: "mis.cifras" }],
    "CE-079": [["ref.ordinaria"], 3, { 0: "mis.cifras", 1: "mis.cifras", 3: "mis.reforma" }],
    "CE-080": [["ref.agravada"], 2, { 0: "mis.reforma", 2: "mis.reforma", 3: "mis.reforma" }],
    "CE-081": [["ref.limites"], 1, { 0: "mis.reforma", 1: "mis.reforma", 2: "mis.reforma" }],
    "CE-082": [["ref.agravada"], 2, { 1: "mis.reforma", 2: "mis.reforma", 3: "mis.reforma" }]
  };

  B.questions.forEach(function (q) {
    var t = T[q.id];
    if (!t && q.official && q.concepts) t = [q.concepts, q.diff, q.mis];
    if (!t) throw new Error("Pregunta sin etiquetas: " + q.id);
    t[0].forEach(function (c) { if (!B.concepts[c]) throw new Error("Concepto desconocido " + c + " en " + q.id); });
    q.concepts = t[0];
    q.diff = t[1];
    q.mis = t[2];
    q.area = q.sub;
  });

  // Esquema visual por concepto (se muestra en la explicación).
  B.esquemaFor = {
    "est.estructura": "estructura", "est.fechas": "historia", "est.reformas": "historia",
    "tp.valores": "valores", "tp.soberania": "valores", "tp.art9": "art9",
    "tp.autonomia": "preliminar", "tp.lenguas": "preliminar", "tp.simbolos": "preliminar", "tp.partidos": "preliminar", "tp.ffaa": "preliminar",
    "df.titulo1": "titulo1", "df.igualdad": "titulo1", "df.vida_religion": "titulo1", "df.legalidad": "titulo1", "df.educacion": "titulo1", "df.participacion": "titulo1",
    "df.detencion": "derechos", "df.intimidad": "derechos", "df.expresion": "derechos", "df.reunion": "derechos",
    "df.nacionalidad": "nacionalidad", "df.extranjeros": "nacionalidad",
    "dc.deberes": "titulo1", "dc.rectores": "titulo1", "gs.tutela": "titulo1",
    "gs.defensor": "defensor", "gs.suspension": "suspension", "gs.estados": "estados",
    "co.funciones": "corona", "co.refrendo": "corona", "co.sucesion": "sucesion", "co.regencia": "sucesion",
    "cg.composicion": "cortes", "cg.funcionamiento": "cortes_func", "cg.leyes": "leyes", "cg.tratados": "tratados",
    "ga.gobierno": "gobierno", "ga.relaciones": "gobierno_cortes", "ga.administracion": "administracion",
    "pj.principios": "poder_judicial", "pj.cgpj": "cgpj", "pj.ts_fiscal": "nombramientos",
    "eh.hacienda": "hacienda",
    "ot.principios": "territorial", "ot.local": "territorial", "ot.control": "territorial", "ot.estatutos": "competencias", "ot.competencias": "competencias",
    "tc.composicion": "tc", "tc.competencias": "tc",
    "ref.iniciativa": "reforma", "ref.ordinaria": "reforma", "ref.agravada": "reforma", "ref.limites": "reforma"
  };

  // Formularios de control (diagnóstico y control de progreso) para el experimento.
  // Equilibrados por área. Se excluyen de la práctica hasta completar ambos.
  B.controlForms = {
    A: ["CE-003", "CE-005", "CE-014", "CE-021", "CE-029", "CE-033", "CE-043", "CE-058", "CE-069", "CE-078"],
    B: ["CE-002", "CE-009", "CE-016", "CE-020", "CE-028", "CE-034", "CE-044", "CE-063", "CE-074", "CE-081"]
  };
})();
