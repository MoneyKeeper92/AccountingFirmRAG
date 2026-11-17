/*
 * Tesón · esquemas visuales (v1)
 * Tablas comparativas que acompañan a las explicaciones. Contenido estático y
 * revisable: cada celda cita el artículo de la Constitución en que se basa.
 */
(function () {
  window.TESON_ESQUEMAS = {
    reforma: {
      title: "Reforma constitucional: ordinaria frente a agravada",
      html:
        '<table class="esq"><thead><tr><th></th><th>Ordinaria <small>art. 167</small></th><th>Agravada <small>art. 168</small></th></tr></thead><tbody>' +
        "<tr><th>Cuándo se usa</th><td>Cualquier reforma que no sea del art. 168</td><td>Revisión total, o parcial que afecte al Título Preliminar, a la Sección 1ª del Capítulo II del Título I o al Título II (la Corona)</td></tr>" +
        "<tr><th>Iniciativa <small>art. 166</small></th><td colspan=\"2\">Gobierno, Congreso, Senado y Asambleas de las CCAA (art. 87.1 y 2). <b>Nunca iniciativa popular.</b></td></tr>" +
        "<tr><th>Aprobación</th><td><b>3/5</b> de cada Cámara. Si no hay acuerdo: Comisión paritaria. Si aún no: mayoría absoluta del Senado + <b>2/3</b> del Congreso</td><td>Principio aprobado por <b>2/3</b> de cada Cámara → <b>disolución inmediata</b> de las Cortes → las nuevas Cámaras ratifican y aprueban el texto por <b>2/3</b></td></tr>" +
        "<tr><th>Referéndum</th><td>Solo si lo pide <b>1/10</b> de los miembros de cualquier Cámara en los <b>15 días</b> siguientes</td><td><b>Siempre</b> (obligatorio)</td></tr>" +
        "<tr><th>Prohibido iniciarla <small>art. 169</small></th><td colspan=\"2\">En tiempo de guerra o durante los estados de alarma, excepción o sitio</td></tr>" +
        "</tbody></table>"
    },
    estados: {
      title: "Estados de alarma, excepción y sitio (art. 116)",
      html:
        '<table class="esq"><thead><tr><th></th><th>Alarma</th><th>Excepción</th><th>Sitio</th></tr></thead><tbody>' +
        "<tr><th>Quién lo declara</th><td>El Gobierno, por decreto en Consejo de Ministros</td><td>El Gobierno, por decreto, <b>previa autorización</b> del Congreso</td><td>El <b>Congreso</b>, por mayoría absoluta, a propuesta exclusiva del Gobierno</td></tr>" +
        "<tr><th>Duración</th><td>Máximo <b>15 días</b>; la prórroga necesita autorización del Congreso</td><td>Máximo <b>30 días</b>, prorrogable por otros 30</td><td>La que fije el Congreso, con su ámbito y condiciones</td></tr>" +
        "<tr><th>Papel del Congreso</th><td>Se le da cuenta</td><td>Autoriza antes</td><td>Lo declara</td></tr>" +
        "<tr><th>Suspensión de derechos <small>art. 55.1</small></th><td>No prevista</td><td>Sí, salvo el art. 17.3</td><td>Sí</td></tr>" +
        "</tbody></table>"
    },
    titulo1: {
      title: "Título I: estructura y nivel de protección",
      html:
        '<table class="esq"><thead><tr><th>Parte</th><th>Artículos</th><th>Protección</th></tr></thead><tbody>' +
        "<tr><th>Capítulo I</th><td>11–13 · Españoles y extranjeros</td><td>—</td></tr>" +
        "<tr><th>Capítulo II, sin sección</th><td><b>14</b> · Igualdad</td><td>Vincula a todos los poderes; ley que respete su contenido esencial; procedimiento preferente y sumario; <b>amparo</b></td></tr>" +
        "<tr><th>Capítulo II, Sección 1ª</th><td><b>15–29</b> · Derechos fundamentales y libertades públicas</td><td>Lo mismo que el art. 14, y además reforma por la vía <b>agravada</b> (art. 168)</td></tr>" +
        "<tr><th>Capítulo II, Sección 2ª</th><td><b>30–38</b> · Derechos y deberes de los ciudadanos</td><td>Vincula a todos los poderes; ley que respete su contenido esencial. Sin amparo, <b>salvo la objeción de conciencia</b> (art. 30)</td></tr>" +
        "<tr><th>Capítulo III</th><td><b>39–52</b> · Principios rectores</td><td>Informan la legislación, la práctica judicial y la actuación de los poderes públicos; solo se alegan ante los jueces según las leyes que los desarrollen</td></tr>" +
        "<tr><th>Capítulo IV</th><td>53–54 · Garantías</td><td>Defensor del Pueblo (art. 54)</td></tr>" +
        "<tr><th>Capítulo V</th><td>55 · Suspensión</td><td>—</td></tr>" +
        "</tbody></table>" +
        '<p class="esq-note">Ojo: el art. 14 tiene amparo, pero no está protegido por la reforma agravada, que solo cubre la Sección 1ª.</p>'
    },
    suspension: {
      title: "Qué derechos pueden suspenderse (art. 55)",
      html:
        '<table class="esq"><thead><tr><th>Supuesto</th><th>Derechos</th><th>Condiciones</th></tr></thead><tbody>' +
        "<tr><th>Estado de excepción o de sitio <small>55.1</small></th><td>17 · 18.2 y 18.3 · 19 · 20.1 a) y d) y 20.5 · 21 · 28.2 · 37.2</td><td>En el estado de excepción <b>no</b> se suspende el art. 17.3 (derechos del detenido)</td></tr>" +
        "<tr><th>Suspensión individual <small>55.2</small></th><td>17.2 · 18.2 · 18.3</td><td>Por ley orgánica, para investigaciones sobre bandas armadas o elementos terroristas, con intervención judicial y control parlamentario</td></tr>" +
        "<tr><th>Nunca suspendibles (ejemplos)</th><td>14 · 15 · 16 · 22 (asociación) · 23 · 24</td><td>No figuran en el art. 55</td></tr>" +
        "</tbody></table>" +
        '<p class="esq-note">Reunión (art. 21) sí; asociación (art. 22) no. En el estado de alarma no hay suspensión de derechos.</p>'
    }
  };
})();
