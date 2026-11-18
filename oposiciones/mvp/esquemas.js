/*
 * Tesón · esquemas visuales (v2)
 * Uno por idea, en frases y no en oraciones: el esquema ancla, la explicación explica.
 * Pensados para el móvil (sin tablas anchas). Cada dato cita su artículo de la Constitución.
 * Colores de serie fijos por institución: Congreso, Senado, Gobierno, CGPJ (validados para daltonismo).
 */
(function () {
  // ── Piezas ───────────────────────────────────────────────────
  function esc(s) { return String(s); }
  function row(label, value) { return '<div class="vz-row"><span>' + label + "</span><b>" + value + "</b></div>"; }
  function card(title, sub, body, tone) {
    return '<div class="vz-card' + (tone ? " " + tone : "") + '"><div class="vz-h">' + title + (sub ? "<small>" + sub + "</small>" : "") + "</div>" + body + "</div>";
  }
  function cols(cards) { return '<div class="vz-cols">' + cards.join("") + "</div>"; }
  function list(items, kind) {
    return '<ul class="vz-list ' + (kind || "") + '">' + items.map(function (i) { return "<li>" + i + "</li>"; }).join("") + "</ul>";
  }
  function note(t) { return '<p class="vz-note">' + t + "</p>"; }
  function label(t) { return '<p class="vz-label">' + t + "</p>"; }
  function big(n, t) { return '<div class="vz-big"><b>' + n + "</b><span>" + t + "</span></div>"; }
  function steps(items) {
    return '<ol class="vz-steps">' + items.map(function (s) {
      return "<li><b>" + s[0] + "</b>" + (s[1] ? "<span>" + s[1] + "</span>" : "") + "</li>";
    }).join("") + "</ol>";
  }
  // Segmented bar: one whole split into parts. parts: [value, name, seriesClass]
  function seg(caption, parts) {
    var total = parts.reduce(function (a, p) { return a + p[0]; }, 0);
    var aria = caption + ": " + parts.map(function (p) { return p[1] + " " + p[0]; }).join(", ");
    return '<figure class="vz-seg"><figcaption>' + caption + '</figcaption><div class="vz-segbar" role="img" aria-label="' + aria + '">' +
      parts.map(function (p) { return '<span class="' + p[2] + '" style="flex:' + p[0] + '" title="' + p[1] + ": " + p[0] + " de " + total + '">' + p[0] + "</span>"; }).join("") +
      '</div><div class="vz-legend">' + parts.map(function (p) { return '<span><i class="' + p[2] + '"></i>' + p[1] + "</span>"; }).join("") + "</div></figure>";
  }
  // Horizontal bars of one series. rows: [label, value, max, valueText, note]
  function bars(caption, rows) {
    return '<figure class="vz-bars"><figcaption>' + caption + "</figcaption>" + rows.map(function (r) {
      var w = Math.max(2, Math.round(100 * r[1] / r[2]));
      return '<div class="vz-bar" title="' + r[0] + ": " + r[3] + '"><span class="vz-bl">' + r[0] + '</span><span class="vz-bt"><i style="width:' + w + '%"></i></span><span class="vz-bv">' + r[3] + "</span>" +
        (r[4] ? '<span class="vz-bn">' + r[4] + "</span>" : "") + "</div>";
    }).join("") + "</figure>";
  }
  // Who proposes → who appoints. rows: [cargo, propone, nombra]
  function who(rows) {
    return '<div class="vz-who">' + rows.map(function (r) {
      return '<div class="vz-whorow"><b>' + r[0] + '</b><span class="vz-flow"><span>' + r[1] + '</span><i aria-hidden="true">→</i><span>' + r[2] + "</span></span></div>";
    }).join("") + "</div>";
  }
  // Protection ladder: [part, arts, what, level 0–4, protections]
  function ladder(rows) {
    return '<div class="vz-ladder">' + rows.map(function (r) {
      var dots = ""; for (var i = 0; i < 4; i++) dots += '<i class="' + (i < r[3] ? "on" : "") + '"></i>';
      return '<div class="vz-lrow"><div class="vz-lhead"><b>' + r[0] + "</b><small>" + r[1] + '</small><span class="vz-dots" aria-label="Protección ' + r[3] + ' de 4">' + dots + "</span></div><div>" + r[2] + "</div>" + (r[4] ? '<div class="vz-lprot">' + r[4] + "</div>" : "") + "</div>";
    }).join("") + "</div>";
  }

  var S = { co: "s-congreso", se: "s-senado", go: "s-gobierno", cg: "s-cgpj", ne: "s-neutral" };

  window.TESON_ESQUEMAS = {
    // ── Estructura ─────────────────────────────────────────────
    estructura: {
      title: "Mapa de la Constitución: 169 artículos",
      area: "EST",
      html:
        bars("Artículos por título", [
          ["Preliminar", 9, 46, "1–9"],
          ["I · Derechos y deberes", 46, 46, "10–55"],
          ["II · Corona", 10, 46, "56–65"],
          ["III · Cortes Generales", 31, 46, "66–96"],
          ["IV · Gobierno y Administración", 11, 46, "97–107"],
          ["V · Gobierno y Cortes", 9, 46, "108–116"],
          ["VI · Poder Judicial", 11, 46, "117–127"],
          ["VII · Economía y Hacienda", 9, 46, "128–136"],
          ["VIII · Organización territorial", 22, 46, "137–158"],
          ["IX · Tribunal Constitucional", 7, 46, "159–165"],
          ["X · Reforma", 4, 46, "166–169"]
        ]) +
        cols([card("Además", "", row("Disposiciones adicionales", "4") + row("Transitorias", "9") + row("Derogatoria", "1") + row("Final", "1"))]) +
        note("Un Título Preliminar y diez títulos. El más largo, el I (46 artículos); el más corto, el X (4).")
    },
    historia: {
      title: "Fechas y reformas",
      area: "EST",
      html:
        label("De la aprobación a la entrada en vigor") +
        steps([
          ["31 oct 1978", "Aprobada por las Cortes"],
          ["6 dic 1978", "Ratificada por el pueblo español en referéndum"],
          ["27 dic 1978", "Sancionada por el Rey"],
          ["29 dic 1978", "Publicada en el BOE: entra en vigor ese día (disposición final)"]
        ]) +
        label("Tres reformas, todas por la vía ordinaria (art. 167)") +
        steps([
          ["1992 · art. 13.2", "Sufragio pasivo de extranjeros en elecciones municipales"],
          ["2011 · art. 135", "Estabilidad presupuestaria"],
          ["2024 · art. 49", "«Personas con discapacidad»"]
        ])
    },

    // ── Título Preliminar ──────────────────────────────────────
    valores: {
      title: "Artículo 1: Estado, valores, soberanía y forma política",
      area: "TP",
      html:
        cols([
          card("España se constituye en", "art. 1.1", "<p class=\"vz-strong\">Estado social y democrático de Derecho</p>"),
          card("Soberanía nacional", "art. 1.2", "<p class=\"vz-strong\">Reside en el pueblo español</p><p class=\"vz-sub\">del que emanan los poderes del Estado</p>"),
          card("Forma política", "art. 1.3", "<p class=\"vz-strong\">Monarquía parlamentaria</p>")
        ]) +
        cols([
          card("Valores superiores", "art. 1.1 · son 4", list(["Libertad", "Justicia", "Igualdad", "Pluralismo político"], "ok"), "tone-ok"),
          card("No son valores superiores", "trampas habituales", list(["Dignidad de la persona <small>art. 10</small>", "Seguridad jurídica <small>art. 9.3</small>", "Solidaridad <small>art. 2</small>"], "no"), "tone-no")
        ])
    },
    art9: {
      title: "Artículo 9",
      area: "TP",
      html:
        cols([
          card("Sujeción", "art. 9.1", "<p>Ciudadanos y poderes públicos, a la Constitución y al resto del ordenamiento</p>"),
          card("Igualdad real", "art. 9.2", "<p>Los poderes públicos promueven libertad e igualdad <b>reales y efectivas</b></p>")
        ]) +
        card("La Constitución garantiza", "art. 9.3 · son 7", list([
          "Legalidad", "Jerarquía normativa", "Publicidad de las normas",
          "Irretroactividad de las disposiciones sancionadoras no favorables o restrictivas de derechos individuales",
          "Seguridad jurídica", "Responsabilidad", "Interdicción de la arbitrariedad de los poderes públicos"
        ], "ok"))
    },
    preliminar: {
      title: "Título Preliminar, artículo por artículo",
      area: "TP",
      html:
        '<div class="vz-rows">' +
        row("Art. 2", "Unidad de la Nación · autonomía · solidaridad") +
        row("Art. 3", "Castellano oficial: deber de conocerlo, derecho a usarlo. Otras lenguas: oficiales en sus CCAA") +
        row("Art. 4", "Bandera: roja, amarilla y roja (amarilla de doble anchura)") +
        row("Art. 5", "Capital: la villa de Madrid") +
        row("Art. 6", "Partidos: pluralismo político, instrumento fundamental de participación") +
        row("Art. 7", "Sindicatos y asociaciones empresariales") +
        row("Art. 8", "FFAA: soberanía e independencia, integridad territorial, ordenamiento constitucional") +
        row("Art. 9", "Sujeción a la Constitución y principios del 9.3") +
        "</div>" +
        note("Partidos (art. 6) y sindicatos (art. 7): estructura interna y funcionamiento democráticos.")
    },

    // ── Título I ───────────────────────────────────────────────
    titulo1: {
      title: "Título I: estructura y nivel de protección",
      area: "DF",
      html:
        ladder([
          ["Capítulo I", "arts. 11–13", "Españoles y extranjeros", 0, ""],
          ["Art. 14", "Cap. II", "Igualdad ante la ley", 3, "Ley orgánica · amparo · procedimiento preferente y sumario"],
          ["Cap. II · Sección 1ª", "arts. 15–29", "Derechos fundamentales y libertades públicas", 4, "Lo mismo que el 14 + reforma agravada (art. 168)"],
          ["Cap. II · Sección 2ª", "arts. 30–38", "Derechos y deberes de los ciudadanos", 2, "Ley que respete su contenido esencial · recurso de inconstitucionalidad · amparo solo la objeción de conciencia (30.2)"],
          ["Capítulo III", "arts. 39–52", "Principios rectores", 1, "Informan legislación, práctica judicial y actuación de los poderes públicos"],
          ["Capítulo IV", "arts. 53–54", "Garantías · Defensor del Pueblo", 0, ""],
          ["Capítulo V", "art. 55", "Suspensión de derechos", 0, ""]
        ]) +
        note("El art. 14 tiene amparo, pero la reforma agravada solo protege la Sección 1ª.")
    },
    derechos: {
      title: "Quién autoriza: juez, nadie o la ley",
      area: "DF",
      html:
        '<div class="vz-rows">' +
        row("Detención preventiva <small>17.2</small>", "Máximo 72 horas") +
        row("Prisión provisional <small>17.4</small>", "Plazo máximo: lo fija la ley") +
        row("Habeas corpus <small>17.4</small>", "Ley: puesta a disposición judicial inmediata") +
        row("Entrar en un domicilio <small>18.2</small>", "Consentimiento, resolución judicial o flagrante delito") +
        row("Comunicaciones <small>18.3</small>", "Secreto, salvo resolución judicial") +
        row("Secuestro de publicaciones <small>20.5</small>", "Solo resolución judicial") +
        row("Reunión pacífica <small>21.1</small>", "Sin autorización previa") +
        row("Manifestaciones <small>21.2</small>", "Comunicación previa a la autoridad") +
        row("Asociaciones <small>22</small>", "Registro solo a efectos de publicidad; disolución o suspensión solo por resolución judicial motivada") +
        "</div>"
    },
    nacionalidad: {
      title: "Nacionalidad, mayoría de edad y extranjeros",
      area: "DF",
      html:
        '<div class="vz-rows">' +
        row("Mayoría de edad <small>12</small>", "18 años") +
        row("Españoles de origen <small>11.2</small>", "No pueden ser privados de su nacionalidad") +
        row("Doble nacionalidad <small>11.3</small>", "Países iberoamericanos y con especial vinculación") +
        row("Derechos del art. 23 <small>13.2</small>", "Solo españoles, salvo sufragio activo y pasivo en municipales (tratado o ley, reciprocidad)") +
        row("Extradición <small>13.3</small>", "Tratado o ley, reciprocidad; nunca por delitos políticos (el terrorismo no lo es)") +
        row("Asilo <small>13.4</small>", "Lo regula la ley") +
        "</div>"
    },
    suspension: {
      title: "Qué derechos pueden suspenderse (art. 55)",
      area: "GS",
      html:
        cols([
          card("Estado de excepción o de sitio", "art. 55.1", list(["17 <small>libertad y detención</small>", "18.2 y 18.3 <small>domicilio y comunicaciones</small>", "19 <small>residencia y circulación</small>", "20.1 a) y d), 20.5 <small>expresión e información</small>", "21 <small>reunión</small>", "28.2 <small>huelga</small>", "37.2 <small>conflicto colectivo</small>"], "ok"), "tone-ok"),
          card("Nunca suspendibles (ejemplos)", "no están en el art. 55", list(["14 <small>igualdad</small>", "15 <small>vida</small>", "16 <small>libertad religiosa</small>", "22 <small>asociación</small>", "23 <small>participación</small>", "24 <small>tutela judicial</small>"], "no"), "tone-no")
        ]) +
        card("Suspensión individual", "art. 55.2 · ley orgánica", "<p>17.2, 18.2 y 18.3 para investigaciones de bandas armadas o terroristas, con intervención judicial y control parlamentario</p>") +
        note("En el estado de excepción no se suspende el 17.3 (derechos del detenido). En el de alarma no se suspenden derechos.")
    },
    estados: {
      title: "Estados de alarma, excepción y sitio (art. 116)",
      area: "GS",
      html:
        cols([
          card("Alarma", "116.2", row("Declara", "Gobierno, por decreto") + row("Congreso", "Se le da cuenta") + row("Duración", "15 días máx.") + row("Prórroga", "Autoriza el Congreso") + row("Derechos", "No se suspenden")),
          card("Excepción", "116.3", row("Declara", "Gobierno, por decreto") + row("Congreso", "Autoriza antes") + row("Duración", "30 días máx.") + row("Prórroga", "Otros 30") + row("Derechos", "Sí (art. 55.1)")),
          card("Sitio", "116.4", row("Declara", "Congreso") + row("Mayoría", "Absoluta") + row("Propone", "Solo el Gobierno") + row("Duración", "La que fije el Congreso") + row("Derechos", "Sí (art. 55.1)"))
        ]) +
        note("Mientras dure cualquiera de los tres, el Congreso no puede disolverse (116.5).")
    },
    defensor: {
      title: "Defensor del Pueblo (art. 54)",
      area: "GS",
      html:
        '<div class="vz-rows">' +
        row("Qué es", "Alto comisionado de las Cortes Generales") +
        row("Quién lo designa", "Las Cortes Generales") +
        row("Para qué", "Defender los derechos del Título I") +
        row("Cómo", "Supervisa la actividad de la Administración") +
        row("Da cuenta a", "Las Cortes Generales") +
        row("Puede interponer", "Recurso de inconstitucionalidad y de amparo (art. 162)") +
        "</div>" +
        note("Lo regula una ley orgánica (LO 3/1981).")
    },

    // ── Corona ─────────────────────────────────────────────────
    corona: {
      title: "Funciones del Rey (arts. 56, 62–65)",
      area: "CO",
      html:
        cols([
          card("Con las Cortes", "art. 62", list(["Sancionar y promulgar las leyes", "Convocar y disolver las Cortes y convocar elecciones", "Convocar a referéndum"])),
          card("Con el Gobierno", "art. 62", list(["Proponer al candidato a Presidente, nombrarlo y cesarlo", "Nombrar y separar Ministros, a propuesta del Presidente", "Expedir decretos del Consejo de Ministros", "Presidir el Consejo de Ministros, a petición del Presidente"])),
          card("Estado y exterior", "arts. 62–63", list(["Mando supremo de las Fuerzas Armadas", "Derecho de gracia (sin indultos generales)", "Acreditar embajadores", "Manifestar el consentimiento en los tratados", "Declarar la guerra y hacer la paz, previa autorización de las <b>Cortes Generales</b>"]))
        ]) +
        cols([
          card("Refrendo", "art. 64", row("Por regla general", "Presidente del Gobierno y, en su caso, Ministros") + row("Propuesta y nombramiento del Presidente, disolución del 99.5", "Presidente del Congreso")),
          card("No le corresponde", "trampas", list(["Aprobar o refrendar leyes", "Dirigir la Administración (Gobierno, art. 97)", "Declarar la guerra con autorización del Gobierno"], "no"), "tone-no")
        ]) +
        note("Art. 65: recibe una cantidad global de los Presupuestos y la distribuye libremente; nombra y releva libremente a su Casa.")
    },
    sucesion: {
      title: "Sucesión, Regencia y tutela (arts. 57–60)",
      area: "CO",
      html:
        label("Orden de sucesión (57.1)") +
        steps([["Primogenitura y representación", ""], ["Línea anterior antes que las posteriores", ""], ["En la misma línea, el grado más próximo", ""], ["En el mismo grado, el varón a la mujer", ""], ["En el mismo sexo, la persona de más edad", ""]]) +
        '<div class="vz-rows">' +
        row("Heredero <small>57.2</small>", "Príncipe de Asturias") +
        row("Extinguidas todas las líneas <small>57.3</small>", "Proveen las Cortes Generales") +
        row("Abdicaciones, renuncias y dudas <small>57.5</small>", "Ley orgánica") +
        row("Consorte <small>58</small>", "Sin funciones constitucionales, salvo la Regencia") +
        "</div>" +
        cols([
          card("Regencia", "art. 59", row("Rey menor", "Padre o madre; si no, pariente mayor de edad más próximo a suceder") + row("Rey inhabilitado", "Príncipe heredero si es mayor de edad") + row("Si no hay nadie", "Las Cortes nombran 1, 3 o 5 personas") + row("Requisitos", "Español y mayor de edad")),
          card("Tutela del Rey menor", "art. 60", row("Primero", "Quien designe el testamento del Rey difunto") + row("Si no", "Padre o madre, mientras sigan viudos") + row("En su defecto", "Las Cortes Generales"))
        ])
    },

    // ── Cortes Generales ───────────────────────────────────────
    cortes: {
      title: "Congreso y Senado: composición",
      area: "CG",
      html:
        cols([
          card('<i class="dot ' + S.co + '"></i>Congreso', "art. 68", big("300–400", "diputados") + row("Circunscripción", "La provincia") + row("Ceuta y Melilla", "1 diputado cada una") + row("Sistema", "Proporcional") + row("Mandato", "4 años")),
          card('<i class="dot ' + S.se + '"></i>Senado', "art. 69", big("4", "senadores por provincia") + row("Islas mayores", "3 (Gran Canaria, Mallorca, Tenerife)") + row("Otras islas", "1 por isla o agrupación") + row("Ceuta y Melilla", "2 cada una") + row("Comunidades Autónomas", "1 + 1 por millón de habitantes") + row("Mandato", "4 años"))
        ]) +
        '<div class="vz-rows">' +
        row("Doble escaño <small>67.1</small>", "Nadie en las dos Cámaras, ni acta autonómica + Congreso") +
        row("Mandato imperativo <small>67.2</small>", "Prohibido") +
        row("Inviolabilidad <small>71.1</small>", "Por las opiniones en el ejercicio de sus funciones") +
        row("Inmunidad <small>71.2</small>", "Solo detenidos en flagrante delito; procesarlos exige autorización de la Cámara") +
        row("Causas penales <small>71.3</small>", "Sala de lo Penal del Tribunal Supremo") +
        "</div>"
    },
    cortes_func: {
      title: "Cómo funcionan las Cámaras",
      area: "CG",
      html:
        label("Periodos ordinarios de sesiones (73.1)") +
        '<div class="vz-months" role="img" aria-label="Periodos de sesiones: septiembre a diciembre y febrero a junio">' +
        ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"].map(function (m, i) { return '<span class="' + ((i >= 8 && i <= 11) || (i >= 1 && i <= 5) ? "on" : "") + '">' + m + "</span>"; }).join("") +
        "</div>" +
        note("Septiembre a diciembre y febrero a junio. Enero, julio y agosto: sin periodo ordinario.") +
        '<div class="vz-rows">' +
        row("Sesiones extraordinarias <small>73.2</small>", "A petición del Gobierno, la Diputación Permanente o la mayoría absoluta de una Cámara") +
        row("Funcionan <small>75.1</small>", "En Pleno y por Comisiones") +
        row("Diputación Permanente <small>78</small>", "Mínimo 21 miembros; vela por los poderes de la Cámara cuando no está reunida") +
        row("Tras disolución o fin del mandato <small>78.3</small>", "Sigue hasta que se constituyen las nuevas Cortes") +
        row("Voto <small>79.3</small>", "Personal e indelegable") +
        row("Plenos <small>80</small>", "Públicos, salvo acuerdo por mayoría absoluta") +
        "</div>"
    },
    leyes: {
      title: "Tipos de normas con rango de ley",
      area: "CG",
      html:
        cols([
          card("Ley orgánica", "art. 81", row("Materias", "Derechos fundamentales, Estatutos, régimen electoral general y las demás previstas") + row("Aprobación", "Mayoría absoluta del Congreso en votación final")),
          card("Ley ordinaria", "", row("Materias", "El resto") + row("Aprobación", "Mayoría simple")),
          card("Decreto legislativo", "arts. 82–85", row("Quién", "Gobierno, por delegación de las Cortes") + row("Ley de bases", "Textos articulados") + row("Ley ordinaria", "Textos refundidos") + row("Nunca", "Materias del art. 81")),
          card("Decreto-ley", "art. 86", row("Cuándo", "Extraordinaria y urgente necesidad") + row("No puede afectar", "Instituciones básicas, derechos del Título I, régimen de las CCAA, Derecho electoral general") + row("Congreso", "Convalida o deroga en 30 días"))
        ]) +
        note("Comisiones legislativas plenas: nunca reforma constitucional, cuestiones internacionales, leyes orgánicas y de bases ni Presupuestos (75.3).")
    },
    procedimiento: {
      title: "Cómo se hace una ley (arts. 87–91)",
      area: "CG",
      html:
        label("Iniciativa (87)") +
        '<div class="vz-rows">' +
        row("Gobierno", "Proyectos de ley (aprobados en Consejo de Ministros)") +
        row("Congreso y Senado", "Proposiciones de ley") +
        row("Asambleas de las CCAA", "Piden un proyecto al Gobierno o remiten una proposición al Congreso") +
        row("Iniciativa popular", "500.000 firmas; nunca en leyes orgánicas, tributarias, internacionales ni gracia") +
        "</div>" +
        label("Tramitación") +
        steps([
          ["Congreso aprueba", ""],
          ["Senado: 2 meses", "Veto (mayoría absoluta) o enmiendas (mayoría simple). Urgentes: 20 días naturales"],
          ["Congreso responde", "Levanta el veto: mayoría absoluta ya, o simple pasados 2 meses"],
          ["Rey: 15 días", "Sanciona, promulga y ordena publicar"]
        ])
    },
    tratados: {
      title: "Tratados internacionales (arts. 93–96)",
      area: "CG",
      html:
        '<div class="vz-rows">' +
        row("Ceder competencias a organizaciones internacionales <small>93</small>", "Ley orgánica") +
        row("Políticos, militares, integridad territorial, derechos del Título I, obligaciones para la Hacienda, o que modifiquen leyes <small>94.1</small>", "Previa autorización de las Cortes Generales") +
        row("El resto <small>94.2</small>", "Se informa a Congreso y Senado") +
        row("Contrario a la Constitución <small>95</small>", "Primero hay que reformarla; Gobierno o Cámaras pueden consultar al TC") +
        row("Validez interna <small>96</small>", "Desde su publicación oficial en España") +
        "</div>"
    },
    mayorias: {
      title: "Mayorías: cuántos votos y para qué",
      area: "CG",
      html:
        bars("Votos necesarios con 350 diputados", [
          ["Absoluta", 176, 350, "176", "Más de la mitad de los miembros"],
          ["Tres quintos", 210, 350, "210", "60 %"],
          ["Dos tercios", 234, 350, "234", "66,7 %"]
        ]) +
        '<div class="vz-rows">' +
        row("Simple", "Más síes que noes. Leyes ordinarias, cuestión de confianza, 2ª votación de investidura") +
        row("Absoluta", "Leyes orgánicas, 1ª votación de investidura, moción de censura, estado de sitio, veto del Senado") +
        row("Tres quintos", "Reforma ordinaria (167); magistrados del TC y vocales del CGPJ que eligen las Cámaras") +
        row("Dos tercios", "Reforma agravada (168); en la ordinaria, el Congreso si el Senado da mayoría absoluta") +
        "</div>" +
        note("El número de diputados (350) lo fija la ley electoral; la Constitución permite entre 300 y 400.")
    },

    // ── Gobierno ───────────────────────────────────────────────
    gobierno: {
      title: "El Gobierno y la investidura",
      area: "GA",
      html:
        cols([
          card("Composición", "art. 98", list(["Presidente", "Vicepresidentes, en su caso", "Ministros", "Los demás miembros que establezca la ley"])),
          card("Funciones", "art. 97", list(["Dirige la política interior y exterior", "La Administración civil y militar", "La defensa del Estado", "Función ejecutiva y potestad reglamentaria"]))
        ]) +
        label("Investidura (art. 99)") +
        steps([
          ["El Rey propone candidato", "Tras consultar a los grupos, a través del Presidente del Congreso"],
          ["1ª votación", "Mayoría absoluta"],
          ["48 horas después", "Mayoría simple"],
          ["Sucesivas propuestas", ""],
          ["2 meses desde la 1ª votación", "El Rey disuelve las Cámaras; refrenda el Presidente del Congreso"]
        ]) +
        '<div class="vz-rows">' +
        row("Cese <small>101</small>", "Elecciones generales, pérdida de confianza, dimisión o fallecimiento del Presidente; sigue en funciones") +
        row("Responsabilidad criminal <small>102</small>", "Sala de lo Penal del TS. Traición o contra la seguridad del Estado: iniciativa de 1/4 del Congreso y mayoría absoluta; sin indulto") +
        "</div>"
    },
    gobierno_cortes: {
      title: "Relaciones entre el Gobierno y las Cortes",
      area: "GA",
      html:
        cols([
          card("Cuestión de confianza", "art. 112", row("La plantea", "El Presidente, previa deliberación del Consejo de Ministros") + row("Se otorga", "Mayoría simple del Congreso")),
          card("Moción de censura", "art. 113", row("La proponen", "Al menos 1/10 de los diputados, con candidato") + row("Se aprueba", "Mayoría absoluta del Congreso") + row("Plazo", "No antes de 5 días; alternativas en los 2 primeros"))
        ]) +
        '<div class="vz-rows">' +
        row("Responsabilidad <small>108</small>", "Solidaria, ante el Congreso de los Diputados") +
        row("Disolución <small>115</small>", "El Presidente, previa deliberación del Consejo de Ministros; nunca durante una moción de censura ni antes de un año") +
        "</div>"
    },
    administracion: {
      title: "La Administración (arts. 103–107)",
      area: "GA",
      html:
        card("Principios de actuación", "art. 103.1", list(["Eficacia", "Jerarquía", "Descentralización", "Desconcentración", "Coordinación"], "ok") + "<p class=\"vz-sub\">Con sometimiento pleno a la ley y al Derecho</p>") +
        '<div class="vz-rows">' +
        row("Acceso a la función pública <small>103.3</small>", "Mérito y capacidad") +
        row("Audiencia y archivos <small>105</small>", "Lo regula la ley") +
        row("Control <small>106</small>", "Los Tribunales; indemnización por el funcionamiento de los servicios públicos") +
        row("Supremo órgano consultivo del Gobierno <small>107</small>", "Consejo de Estado (ley orgánica)") +
        "</div>"
    },

    // ── Poder Judicial ─────────────────────────────────────────
    poder_judicial: {
      title: "Poder Judicial: principios (arts. 117–127)",
      area: "PJ",
      html:
        '<div class="vz-rows">' +
        row("La justicia <small>117.1</small>", "Emana del pueblo; se administra en nombre del Rey") +
        row("Jueces y Magistrados <small>117.1</small>", "Independientes, inamovibles, responsables y sometidos únicamente al imperio de la ley") +
        row("Base de los Tribunales <small>117.5</small>", "Unidad jurisdiccional") +
        row("Potestad jurisdiccional <small>117.3</small>", "Exclusiva de Juzgados y Tribunales") +
        row("Procedimiento <small>120</small>", "Predominantemente oral, sobre todo en materia criminal; sentencias motivadas y en audiencia pública") +
        row("Gratuidad <small>119</small>", "Cuando lo diga la ley y siempre sin recursos suficientes") +
        row("Error judicial <small>121</small>", "Indemnización a cargo del Estado") +
        row("Participación <small>125</small>", "Acción popular y Jurado") +
        "</div>"
    },
    cgpj: {
      title: "Consejo General del Poder Judicial (art. 122)",
      area: "PJ",
      html:
        seg("20 vocales, nombrados por el Rey por 5 años", [[12, "Jueces y Magistrados (según la ley orgánica)", S.ne], [4, "A propuesta del Congreso", S.co], [4, "A propuesta del Senado", S.se]]) +
        '<div class="vz-rows">' +
        row("Lo preside", "El Presidente del Tribunal Supremo") +
        row("Qué es", "El órgano de gobierno del Poder Judicial") +
        row("Vocales de las Cámaras", "Tres quintos de cada Cámara; abogados y juristas de reconocida competencia con más de 15 años de ejercicio") +
        "</div>"
    },
    nombramientos: {
      title: "Quién propone y quién nombra",
      area: "PJ",
      html:
        who([
          ["Presidente del Gobierno", "Rey propone · Congreso da la confianza", "Rey"],
          ["Ministros", "Presidente del Gobierno", "Rey"],
          ["Presidente del Tribunal Supremo", "CGPJ", "Rey"],
          ["Fiscal General del Estado", "Gobierno, oído el CGPJ", "Rey"],
          ["Vocales del CGPJ (20)", "12 jueces · 4 Congreso · 4 Senado", "Rey, 5 años"],
          ["Magistrados del TC (12)", "4 Congreso · 4 Senado · 2 Gobierno · 2 CGPJ", "Rey, 9 años"],
          ["Presidente del TC", "El Pleno del Tribunal", "Rey, 3 años"],
          ["Presidente de una CA (vía 151)", "Elegido por la Asamblea", "Rey"],
          ["Defensor del Pueblo", "Las Cortes Generales", "Las Cortes"],
          ["Casa del Rey", "", "El Rey, libremente"]
        ]) +
        note("Casi siempre nombra el Rey; la pregunta suele estar en quién propone.")
    },

    // ── Economía y Hacienda ────────────────────────────────────
    hacienda: {
      title: "Tributos, Presupuestos y deuda (arts. 133–136)",
      area: "EH",
      html:
        cols([
          card("Tributos", "art. 133", row("Potestad originaria", "El Estado, mediante ley") + row("CCAA y entes locales", "Según la Constitución y las leyes") + row("Beneficios fiscales", "En virtud de ley")),
          card("Presupuestos", "art. 134", row("Elabora", "El Gobierno") + row("Aprueban", "Las Cortes") + row("Presentación", "Ante el Congreso, 3 meses antes de que expiren los anteriores") + row("Si no se aprueban", "Prórroga automática") + row("Tributos", "No puede crearlos; sí modificarlos si lo prevé una ley tributaria"))
        ]) +
        '<div class="vz-rows">' +
        row("Deuda pública <small>135.3</small>", "Estado y CCAA, autorizados por ley; intereses y capital con prioridad absoluta") +
        row("Tribunal de Cuentas <small>136</small>", "Supremo órgano fiscalizador; depende de las Cortes Generales") +
        "</div>"
    },

    // ── Organización territorial ───────────────────────────────
    territorial: {
      title: "Organización territorial (arts. 137–158)",
      area: "OT",
      html:
        cols([
          card("Municipio", "art. 140", row("Gobierno", "Ayuntamiento: Alcalde y Concejales") + row("Naturaleza", "Autonomía y personalidad jurídica plena")),
          card("Provincia", "art. 141", row("Qué es", "Agrupación de municipios y división territorial del Estado") + row("Gobierno", "Diputaciones u otras corporaciones representativas") + row("Cambiar límites", "Cortes, por ley orgánica") + row("Islas", "Cabildos o Consejos")),
          card("Comunidad Autónoma", "arts. 143–158", row("Norma básica", "Su Estatuto") + row("Representación ordinaria del Estado", "El Presidente de la CA (152.1)") + row("Administración del Estado en la CA", "Delegado del Gobierno (154)"))
        ]) +
        '<div class="vz-rows">' +
        row("Principios <small>137–139</small>", "Autonomía, solidaridad, sin privilegios, igualdad de derechos en todo el territorio") +
        row("Control de las CCAA <small>153</small>", "TC, Gobierno (con dictamen del Consejo de Estado), contencioso-administrativo y Tribunal de Cuentas") +
        row("Incumplimiento grave <small>155</small>", "Gobierno, previo requerimiento y con mayoría absoluta del Senado") +
        "</div>"
    },
    competencias: {
      title: "Competencias: Comunidades Autónomas y Estado",
      area: "OT",
      html:
        cols([
          card("Pueden asumir las CCAA", "art. 148 · ejemplos", list(["Ordenación del territorio, urbanismo y vivienda", "Montes y aprovechamientos forestales", "Agricultura y ganadería", "Turismo, deporte y ocio", "Asistencia social", "Sanidad e higiene"], "ok"), "tone-ok"),
          card("Exclusivas del Estado", "art. 149.1 · ejemplos", list(["Nacionalidad, extranjería y asilo", "Relaciones internacionales y defensa", "Administración de Justicia", "Legislación mercantil, penal, procesal y laboral", "Legislación básica y régimen económico de la Seguridad Social", "Tráfico y circulación de vehículos a motor", "Marina mercante, armas y explosivos"]))
        ]) +
        '<div class="vz-rows">' +
        row("Ley marco <small>150.1</small>", "Las Cortes atribuyen a las CCAA dictar normas en materia estatal") +
        row("Transferencia o delegación <small>150.2</small>", "Ley orgánica") +
        row("Armonización <small>150.3</small>", "Mayoría absoluta de cada Cámara") +
        row("Estatutos <small>147</small>", "Norma institucional básica; reforma: su procedimiento + ley orgánica de las Cortes") +
        row("Interés nacional <small>144</small>", "Las Cortes, por ley orgánica, pueden autorizar o acordar Estatutos especiales") +
        "</div>"
    },

    // ── Tribunal Constitucional ────────────────────────────────
    tc: {
      title: "Tribunal Constitucional (arts. 159–165)",
      area: "TC",
      html:
        seg("12 magistrados, nombrados por el Rey", [[4, "Congreso (3/5)", S.co], [4, "Senado (3/5)", S.se], [2, "Gobierno", S.go], [2, "CGPJ", S.cg]]) +
        '<div class="vz-rows">' +
        row("Mandato <small>159.3</small>", "9 años; se renueva por terceras partes cada 3") +
        row("Requisitos <small>159.2</small>", "Juristas de reconocida competencia con más de 15 años de ejercicio") +
        row("Presidente <small>160</small>", "Lo propone el Pleno; lo nombra el Rey; 3 años") +
        row("Competencias <small>161</small>", "Recurso de inconstitucionalidad, amparo, conflictos de competencia Estado–CCAA") +
        "</div>" +
        cols([
          card("Recurso de inconstitucionalidad", "162.1.a", list(["Presidente del Gobierno", "Defensor del Pueblo", "50 diputados", "50 senadores", "Gobiernos y, en su caso, Asambleas de las CCAA"])),
          card("Recurso de amparo", "162.1.b", list(["Toda persona con interés legítimo", "Defensor del Pueblo", "Ministerio Fiscal"]))
        ])
    },

    // ── Reforma ────────────────────────────────────────────────
    reforma: {
      title: "Reforma constitucional: ordinaria frente a agravada",
      area: "REF",
      html:
        cols([
          card("Ordinaria", "art. 167", steps([["3/5 de cada Cámara", ""], ["Si no hay acuerdo", "Comisión paritaria Congreso-Senado"], ["Si aún no", "Mayoría absoluta del Senado + 2/3 del Congreso"], ["Referéndum", "Solo si lo pide 1/10 de una Cámara en 15 días"]])),
          card("Agravada", "art. 168", steps([["Principio: 2/3 de cada Cámara", ""], ["Disolución inmediata de las Cortes", ""], ["Nuevas Cámaras: ratifican y aprueban por 2/3", ""], ["Referéndum siempre", ""]]))
        ]) +
        '<div class="vz-rows">' +
        row("Cuándo la agravada", "Revisión total, o parcial del Título Preliminar, Cap. II Sec. 1ª del Título I o Título II") +
        row("Iniciativa <small>166</small>", "Gobierno, Congreso, Senado y Asambleas de las CCAA. Nunca popular") +
        row("Prohibido iniciarla <small>169</small>", "En guerra o durante los estados de alarma, excepción o sitio") +
        "</div>"
    }
  };
})();
