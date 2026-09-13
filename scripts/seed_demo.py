"""Load the synthetic sample clients into the database using the active profile.

    python scripts/seed_demo.py            # uses FIRM_RAG_PROFILE (default offline)
    FIRM_RAG_PROFILE=anthropic_voyage python scripts/seed_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.main import AppState  # noqa: E402

CLIENTS = {
    "abc_company": dict(name="ABC Company, Inc.", entity_type="s_corp", industry="Wholesale distribution", fiscal_year_end="12-31",
                        notes="Audit client since 2019. Line of credit with First Regional Bank."),
    "john_doe": dict(name="John & Maria Doe", entity_type="individual", industry="W-2 + consulting Schedule C", fiscal_year_end="12-31",
                     notes="1040 client. Consulting LLC may elect S-corp for 2026."),
}
ENGAGEMENT = {"abc_company": "audit", "john_doe": "tax"}


def main() -> None:
    state = AppState(Settings.load())
    print(f"profile={state.settings.profile_name} llm={state.llm.identity} embed={state.embedder.identity}")
    for folder, meta in CLIENTS.items():
        client = state.store.upsert_client(client_id=folder, **meta)
        for f in sorted((ROOT / "sample_data" / folder).iterdir()):
            r = state.pipeline.ingest_bytes(client_id=client["id"], filename=f.name, data=f.read_bytes(), uploaded_by="seed",
                                            engagement=ENGAGEMENT[folder])
            print(f"  {f.name}: {r['status']} type={r.get('doc_type')} year={r.get('tax_year')} chunks={r.get('chunks')} facts={r.get('facts')}")
    print(state.store.stats())


if __name__ == "__main__":
    main()
