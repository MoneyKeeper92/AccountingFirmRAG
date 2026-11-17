"""Build mvp/oficiales.js from content/oficiales_inap_ce.json.

The JSON is the editable source of truth for official INAP questions on the Constitution:
official wording (q, o) copied verbatim from the INAP papers, plus Tesón's own key check,
explanations and tags. Run: python3 oposiciones/tools/build_official.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "content" / "oficiales_inap_ce.json"
OUT = ROOT / "mvp" / "oficiales.js"
BOE = "https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229"

AREA_NAMES = {
    "CO": "La Corona (arts. 56–65)",
    "CG": "Cortes Generales (arts. 66–96)",
    "GA": "Gobierno y Administración (arts. 97–116)",
    "PJ": "Poder Judicial (arts. 117–127)",
    "EH": "Economía y Hacienda (arts. 128–136)",
    "OT": "Organización territorial (arts. 137–158)",
    "TC": "Tribunal Constitucional (arts. 159–165)",
}

data = json.loads(SRC.read_text(encoding="utf-8"))
questions = []
for item in data["questions"]:
    if item.get("outdated"):
        continue  # the official answer no longer matches the current text; never shown
    ref = str(item["ref"])
    q = {
        "id": item["id"], "sub": item["area"], "art": item["art"],
        "q": item["q"], "o": item["o"], "k": item["k"], "ex": item["ex"], "w": item["w"],
        "ref": ref, "tema": "CE1",
        "official": True, "year": item["year"], "paperId": item["paper"], "paperLabel": item["paperLabel"],
        "keyBasis": item["keyBasis"],
        "sourceType": "official_exam_inap", "sourceId": item["paper"], "sourceUrl": item["sourceUrl"],
        "sourceRef": item["sourceRef"],
        "attribution": "Origen de los datos: Instituto Nacional de Administración Pública (INAP)",
        "contentAsOf": data["contentAsOf"], "reviewStatus": item.get("reviewStatus", "pending_human"),
        "url": BOE if ref == "texto" else f"{BOE}#a{ref}",
        "concepts": item["concepts"], "diff": item["diff"], "mis": item.get("mis", {}),
    }
    if item.get("trap"):
        q["trap"] = item["trap"]
    questions.append(q)

js = f"""/*
 * Tesón · preguntas oficiales del INAP sobre la Constitución (generado; no editar a mano).
 * Fuente editable: oposiciones/content/oficiales_inap_ce.json · Generador: oposiciones/tools/build_official.py
 * Enunciados y opciones: literales de los cuestionarios oficiales.
 * Origen de los datos: Instituto Nacional de Administración Pública (INAP). Explicaciones: Tesón.
 */
(function () {{
  var B = window.TESON_BANK;
  var AREA_NAMES = {json.dumps(AREA_NAMES, ensure_ascii=False)};
  Object.keys(AREA_NAMES).forEach(function (k) {{ B.subs[k] = AREA_NAMES[k]; }});
  B.officialSources = {json.dumps(data["papers"], ensure_ascii=False)};
  var Q = {json.dumps(questions, ensure_ascii=False, indent=1)};
  Q.forEach(function (q) {{ B.questions.push(q); }});
}})();
"""
OUT.write_text(js, encoding="utf-8")
print(f"Wrote {OUT.relative_to(ROOT)}: {len(questions)} official questions "
      f"({sum(1 for q in questions if q['keyBasis'] == 'official')} with the official key), "
      f"{sum(1 for i in data['questions'] if i.get('outdated'))} outdated left out.")
