"""Send due reminders for request lists that were sent and still have pending items.

    python scripts/send_reminders.py            # once (run from cron / Task Scheduler each morning)
    python scripts/send_reminders.py --dry-run  # show what would go out

Schedule per list: `reminder_days` (default 7,14,21 days after send / last reminder). A list
with nothing pending is complete and is never reminded. With no SMTP_HOST configured the
reminder is drafted and written to the audit log for a person to send.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.main import AppState, dispatch_reminder  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--firm-name", default="our office")
    args = ap.parse_args()
    state = AppState(Settings.load())
    due = state.store.due_reminders()
    print(f"{len(due)} reminder(s) due")
    for rl in due:
        if args.dry_run:
            print(json.dumps({"list": rl["id"], "client": rl["client_name"], "pending": rl["pending"], "reminder_number": rl["reminder_number"]}))
            continue
        print(json.dumps(dispatch_reminder(state, rl["id"], actor="reminder-job", firm_name=args.firm_name)))


if __name__ == "__main__":
    main()
