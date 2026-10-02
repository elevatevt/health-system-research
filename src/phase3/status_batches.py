"""Write status-pass batches for reviewed full-run systems whose status is "unverified".

Run after `consolidate.py --tag full`. Each batch holds up to 10 systems:
  data/raw/phase3_full/statusbatch_NN.json  ->  agent writes data/raw/phase3_full/status_pass_NN.json
consolidate.py picks up status_*.json files as overrides on the next run.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import OUT, RAW  # noqa: E402

BATCH = 10
PROMPT = """Public-data, read-only web research; no logins or form submissions. Today is {today}.
Read {batch}. For EACH system in it, run one dedicated status search such as
"<system name> merger OR acquisition OR renamed OR closed OR sold 2024 2025 2026", and open the system's About/news page if the result is unclear.
Write a JSON array to {result} with one object per system and ONLY these keys:
system_id, current_name, status_since_2023 (unchanged | renamed | acquired by | merged into | partly closed | closed),
current_parent, status_evidence_url (a current page showing the status), status_change_date,
status_search_query (the exact search you ran), now_for_profit (true if the system was acquired by or converted to a for-profit owner, else false).
Rules: a system that acquired another or merged as the surviving parent is "unchanged" (or "renamed" if its name changed); put the other party in current_parent only if this system was absorbed. Pending deals that have not closed are "unchanged". Every object needs status_search_query and status_evidence_url.
Validate with: C:\\dev\\health-system-research\\.venv\\Scripts\\python.exe -c "import json; print(len(json.load(open(r'{result}', encoding='utf-8'))))"
Reply with only the systems whose status is not "unchanged"."""


def main() -> None:
    df = pd.read_csv(OUT / "phase3_full_classification.csv")
    systems = pd.read_csv(OUT / "phase3_full_systems.csv").set_index("system_id")
    todo = df[(df.status_since_2023 == "unverified")]
    out_dir = RAW / "phase3_full"
    for old in out_dir.glob("statusbatch_*.json"):
        old.unlink()
    n = 0
    for n, start in enumerate(range(0, len(todo), BATCH), 1):
        rows = [{"system_id": r.system_id, "system_name": r.system_name, "hq": f"{systems.hq_city[r.system_id]}, {r.hq_state}",
                 "footprint_states": systems.footprint_states[r.system_id],
                 "name_reported_by_reviewer": r.current_name if isinstance(r.current_name, str) else ""}
                for r in todo.iloc[start:start + BATCH].itertuples()]
        (out_dir / f"statusbatch_{n:02d}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{len(todo)} unverified systems -> {n} batches in {out_dir}")
    print("Agent prompt template (fill {today}, {batch}, {result} = status_pass_NN.json):\n" + PROMPT)


if __name__ == "__main__":
    main()
