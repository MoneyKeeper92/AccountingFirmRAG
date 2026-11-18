"""Build web/src/data/quiz.json: the 10-question free test embedded on tesonopos.es.

Only official INAP questions with the definitive official key. Wording verbatim (typo fixes logged
in content/oficiales_inap_ce.json); explanations, "la clave" and highlight are Tesón's.
Run: python3 oposiciones/tools/build_web_quiz.py
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = ["OF-001", "OF-002", "OF-003", "OF-004", "OF-005", "OF-006", "OF-007", "OF-008", "OF-013", "OF-014"]
AREAS = {"EST": "Estructura", "TP": "Título Preliminar", "REF": "Reforma", "CO": "La Corona", "CG": "Cortes Generales",
         "PJ": "Poder Judicial", "GA": "Gobierno", "OT": "Organización territorial"}

data = json.loads((ROOT / "content" / "oficiales_inap_ce.json").read_text(encoding="utf-8"))
claves = json.loads(re.search(r"window\.TESON_CLAVES = (\{.*\});", (ROOT / "mvp" / "claves.js").read_text(encoding="utf-8"), re.S).group(1))
byid = {q["id"]: q for q in data["questions"]}
out = []
for i in IDS:
    q = byid[i]
    assert q["keyBasis"] == "official" and not q.get("hold") and not q.get("outdated"), i
    out.append({"id": i, "q": q["q"], "o": q["o"], "k": q["k"], "area": AREAS[q["area"]],
                "clave": claves[i]["c"], "ex": q["ex"], "mark": claves[i]["m"],
                "source": q["paperLabel"].split(" · ")[0] + " · " + q["sourceRef"]})
dest = ROOT / "web" / "src" / "data" / "quiz.json"
dest.write_text(json.dumps({"title": "Examen oficial de Auxiliar y Administrativo del Estado, mayo de 2026", "questions": out}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Wrote {dest.relative_to(ROOT)}: {len(out)} questions")
