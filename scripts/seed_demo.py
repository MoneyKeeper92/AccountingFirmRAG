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
    "john_doe": dict(name="John & Maria Doe", entity_type="individual", industry="W-2 employee + consulting Schedule C", fiscal_year_end="12-31",
                     notes="1040 client since 2019. Consulting LLC may elect S-corp for 2026.", engagement="tax_1040"),
    "abc_company": dict(name="ABC Company, Inc.", entity_type="s_corp", industry="Wholesale distribution", fiscal_year_end="12-31",
                        notes="1120-S client, two shareholders 60/40. Related-party warehouse lease.", engagement="tax_1120s"),
    "riverbend_partners": dict(name="Riverbend Partners LLC", entity_type="partnership", industry="Landscaping services + rental building", fiscal_year_end="12-31",
                               notes="1065 client, three partners. Possible partner buyout in 2026.", engagement="tax_1065"),
    "northline_corp": dict(name="Northline Distribution Corp.", entity_type="c_corp", industry="Industrial distribution", fiscal_year_end="12-31",
                           notes="1120 client. Accumulated earnings exposure; CFO handles estimates.", engagement="tax_1120"),
}


def main() -> None:
    state = AppState(Settings.load())
    print(f"profile={state.settings.profile_name} llm={state.llm.identity} embed={state.embedder.identity}")
    for folder, meta in CLIENTS.items():
        meta = dict(meta)
        engagement = meta.pop("engagement")
        client = state.store.upsert_client(client_id=folder, **meta)
        for f in sorted((ROOT / "sample_data" / folder).iterdir()):
            r = state.pipeline.ingest_bytes(client_id=client["id"], filename=f.name, data=f.read_bytes(), uploaded_by="seed", engagement=engagement)
            print(f"  {f.name}: {r['status']} type={r.get('doc_type')} year={r.get('tax_year')} chunks={r.get('chunks')} facts={r.get('facts')}")
    print(state.store.stats())


if __name__ == "__main__":
    main()
