"""Evaluation harness: run a fixed question set against a fixed archive and score it.

    python scripts/run_eval.py                       # seeds a temporary DB with sample_data, runs evals/questions.jsonl
    python scripts/run_eval.py --db data/firm_rag.db # run against an existing archive (no seeding)
    FIRM_RAG_PROFILE=anthropic_voyage python scripts/run_eval.py --out evals/results-opus5.json

Scores per question: citation recall (expected files among the retrieved sources), tool use
(expected tools called), answer contains (expected phrases present). Facts rows check extracted
values against expected numbers. Run before and after any model profile change and diff the
JSON outputs. Extend evals/questions.jsonl with real questions from the audit log.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_questions(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip() and not ln.startswith("#")]


def run(questions: list[dict], state) -> dict:
    from app import forecast

    results = []
    for q in questions:
        if q.get("kind") == "facts":
            series = forecast.series_by_metric(state.store.facts_for_client(q["client_id"]))
            checks = []
            for name, by_year in q["expected_facts"].items():
                for year, expected in by_year.items():
                    got = series.get(name, {}).get(int(year))
                    ok = got is not None and abs(got - expected) <= max(1.0, abs(expected) * 0.001)
                    checks.append({"fact": f"{name}/{year}", "expected": expected, "got": got, "ok": ok})
            score = sum(c["ok"] for c in checks) / len(checks) if checks else 0
            results.append({"id": q["id"], "kind": "facts", "score": round(score, 3), "checks": checks})
            continue
        r = state.rag.ask(q["question"], q.get("client_id"), actor="eval", today=dt.date.today().isoformat())
        cited = {c["filename"] for c in r.citations}
        exp_files = q.get("expected_files", [])
        recall = (sum(any(e in f for f in cited) for e in exp_files) / len(exp_files)) if exp_files else None
        tools_used = {t["tool"] for t in r.tool_trace}
        exp_tools = q.get("expected_tools", [])
        tools_ok = all(t in tools_used for t in exp_tools) if exp_tools else None
        phrases = q.get("expected_answer_contains", [])
        phrase_hits = [p for p in phrases if p.lower() in r.answer.lower()]
        phrase_score = (len(phrase_hits) / len(phrases)) if phrases else None
        parts = [x for x in (recall, 1.0 if tools_ok else 0.0 if tools_ok is not None else None, phrase_score) if x is not None]
        results.append({"id": q["id"], "kind": "question", "score": round(sum(parts) / len(parts), 3) if parts else None,
                        "citation_recall": recall, "tools_ok": tools_ok, "phrase_score": phrase_score,
                        "cited": sorted(cited), "tools": sorted(tools_used), "model": r.model, "usage": r.usage})
    scored = [x["score"] for x in results if x["score"] is not None]
    return {"profile": state.settings.profile_name, "llm": state.llm.identity, "embedding": state.embedder.identity,
            "ran_at": dt.datetime.now().isoformat(timespec="seconds"), "overall": round(sum(scored) / len(scored), 3) if scored else None,
            "results": results}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(ROOT / "evals" / "questions.jsonl"))
    ap.add_argument("--db", default=None, help="existing archive to evaluate; default seeds sample_data into a temp DB")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.db:
        os.environ["FIRM_RAG_DB"] = args.db
    else:
        tmp = tempfile.mkdtemp()
        os.environ["FIRM_RAG_DB"] = f"{tmp}/eval.db"
        os.environ["FIRM_RAG_UPLOADS"] = f"{tmp}/uploads"
    from app.config import Settings
    from app.main import AppState

    state = AppState(Settings.load())
    if not args.db:
        import scripts.seed_demo as seed
        for folder, meta in seed.CLIENTS.items():
            meta = dict(meta); engagement = meta.pop("engagement")
            state.store.upsert_client(client_id=folder, **meta)
            for f in sorted((ROOT / "sample_data" / folder).iterdir()):
                state.pipeline.ingest_bytes(client_id=folder, filename=f.name, data=f.read_bytes(), uploaded_by="eval", engagement=engagement)

    report = run(load_questions(Path(args.questions)), state)
    print(f"profile={report['profile']} llm={report['llm']} overall={report['overall']}")
    for r in report["results"]:
        extra = f"recall={r.get('citation_recall')} tools={r.get('tools_ok')} phrases={r.get('phrase_score')}" if r["kind"] == "question" else f"{sum(c['ok'] for c in r['checks'])}/{len(r['checks'])} facts"
        print(f"  {r['id']:<22} score={r['score']}  {extra}")
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
