# Run pdftotext -layout on research/official_exams_pdfs into TXT first; paths below are from the original run.
"""Extract the Constitution questions from the INAP (AGE) papers listed in constitution_question_map.csv."""
import json, re, sys
from pathlib import Path

TXT = Path("/tmp/claude-0/-home-user-AccountingFirmRAG/04ef1702-38f6-548b-80d7-7f988008f75b/scratchpad/pdftxt")
OUT = Path("/tmp/claude-0/-home-user-AccountingFirmRAG/04ef1702-38f6-548b-80d7-7f988008f75b/scratchpad/ce")

# paper id, file prefix, label, question numbers (first part), reserve numbers (first part)
PAPERS = [
    ("AUX-2026", "02", "Auxiliar Administrativo del Estado (C2), acceso libre, convocatoria 2025 · examen 23/05/2026 · modelo A", [1,2,3,4,5,6,7,9], [2,3], "04"),
    ("ADV-2026", "06", "Administrativo del Estado (C1), acceso libre, convocatoria 2025 · examen 23/05/2026 · modelo A", [1,2,3,4,5,9], [5], "09"),
    ("ADV-2026X", "08", "Administrativo del Estado (C1), acceso libre, convocatoria 2025 · ejercicio extraordinario 2026", [1,2,3,4,5,9,10,19,29], [5], None),
    ("AUX-2024", "11", "Auxiliar Administrativo del Estado (C2), acceso libre, OEP 2023-2024 · examen 14/12/2024 · modelo A", [1,2,3,4,6,10,13], [], None),
    ("AUX-2024X", "13", "Auxiliar Administrativo del Estado (C2), acceso libre, OEP 2023-2024 · ejercicio extraordinario", [1,2,3,4,5,6,7,8,24], [], None),
    ("ADV-2024", "14", "Administrativo del Estado (C1), acceso libre, OEP 2023-2024 · examen 14/12/2024 · modelo A", [1,2,3,4,6,11,18,35], [], None),
    ("ADV-2024X", "16", "Administrativo del Estado (C1), acceso libre, OEP 2023-2024 · ejercicio extraordinario", [1,2,3,4,5,10,11,17,20,24], [4], None),
    ("AUX-2023", "17", "Auxiliar Administrativo del Estado (C2), acceso libre, OEP 2021-2022 · examen septiembre 2023", [1,2,3,4,5,6,7,8,9,15,16], [], None),
    ("ADV-2023", "18", "Administrativo del Estado (C1), acceso libre, OEP 2021-2022 · examen septiembre 2023", [8,15,27,33,34,37], [], None),
    ("ADV-2023X", "19", "Administrativo del Estado (C1), acceso libre, OEP 2021-2022 · ejercicio extraordinario", [1,2,8,10,13,16,19,25], [], None),
    ("AUX-2022", "20", "Auxiliar Administrativo del Estado (C2), acceso libre, OEP 2020 · examen 12/02/2022", [1,2,3,4,5,6,7,8], [3], None),
    ("AUX-2022X", "21", "Auxiliar Administrativo del Estado (C2), acceso libre, OEP 2020 · ejercicio extraordinario", [1,3,5,29], [2], None),
    ("ADV-2022", "22", "Administrativo del Estado (C1), acceso libre, OEP 2020 · examen 12/02/2022", [1,4,6,15], [], None),
    ("ADV-2022X", "23", "Administrativo del Estado (C1), acceso libre, OEP 2020 · ejercicio extraordinario", [1,2,3,4,11], [], None),
]

NOISE = re.compile(r"(Página \d+ de \d+|MODELO [AB]\s*$|^\s*\d{4}\s*-\s*(AUX|ADVO?)|^\s*(AUX|ADVO?)-L|^\s*Cuerpo General)", re.I)
QRE = re.compile(r"^\s{0,6}(\d{1,3})\.\s+(\S.*)$")
ORE = re.compile(r"^\s{0,10}([a-d])\)\s*(.*)$")


def parse_first_part(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next(i for i, l in enumerate(lines) if "PRIMERA PARTE" in l)
    main, reserve, cur = {}, {}, None
    bucket = main
    expanded = []
    for l in lines[start + 1:]:
        parts = re.split(r"\s{2,}(?=[b-d]\)\s)", l)
        expanded.extend(parts)
    for l in expanded:
        if re.search(r"SEGUNDA PARTE|SUPUESTO I\b", l):
            break
        if re.search(r"Preguntas de reserva", l, re.I):
            bucket = reserve
            cur = None
            continue
        if NOISE.search(l) or not l.strip():
            continue
        m = QRE.match(l)
        if m and (cur is None or cur["opts"] and len(cur["opts"]) >= 4 or int(m.group(1)) not in bucket):
            if not (cur and len(cur["opts"]) < 4 and cur["opts"]):
                n = int(m.group(1))
                cur = {"n": n, "q": m.group(2).strip(), "opts": []}
                bucket[n] = cur
                continue
        o = ORE.match(l)
        if o and cur is not None and len(cur["opts"]) < 4 and o.group(1) == "abcd"[len(cur["opts"])]:
            cur["opts"].append(o.group(2).strip())
            continue
        if cur is not None:
            if cur["opts"]:
                cur["opts"][-1] += " " + l.strip()
            else:
                cur["q"] += " " + l.strip()
    return main, reserve


def parse_key(prefix):
    """Left column = first part. Right column: C1 keys list first-part reserves before 'Supuesto'."""
    if not prefix:
        return None, None
    path = next(TXT.glob(prefix + "_*.txt"))
    main, reserve = {}, {}
    right_is_reserve = False
    for l in path.read_text().splitlines():
        if re.match(r"^\s*Primera parte\s+Preguntas de reserva", l):
            right_is_reserve = True
        if re.search(r"Supuesto I\b", l):
            right_is_reserve = False
        hits = re.findall(r"(\d{1,3})\.\s+([a-d]|Anulada)\b", l)
        if hits:
            n, k = hits[0]
            main.setdefault(int(n), k)
            if len(hits) > 1 and right_is_reserve:
                reserve[int(hits[1][0])] = hits[1][1]
    return main, reserve


CE_RE = re.compile(r"Constituci[oó]n|\bCE\b|constitucional")

def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    return s


items = []
for pid, prefix, label, nums, res, keyprefix in PAPERS:
    path = next(TXT.glob(prefix + "_*.txt"))
    main, reserve = parse_first_part(path)
    kmain, kres = parse_key(keyprefix)
    for kind, src, wanted, keys in (("main", main, nums, kmain), ("reserva", reserve, res, kres)):
        cands = sorted(n for n, q in src.items() if CE_RE.search(q["q"] + " " + " ".join(q["opts"])))
        for n in cands:
            q = src.get(n)
            if not q or len(q["opts"]) != 4:
                print(f"!! {pid} {kind} {n}: parse problem: {q}", file=sys.stderr)
                continue
            key = keys.get(n) if keys else None
            items.append({
                "paper": pid, "paperLabel": label, "part": "primera", "reserve": kind == "reserva", "number": n,
                "q": clean(q["q"]), "o": [clean(x).rstrip() for x in q["opts"]],
                "officialKey": ("abcd".index(key) if key and key in "abcd" else ("annulled" if key == "Anulada" else None)),
                "pdf": path.name.replace(".txt", ".pdf"),
            })

(OUT / "extracted.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
print(len(items), "questions;", sum(1 for i in items if i["officialKey"] is not None), "with official key")
