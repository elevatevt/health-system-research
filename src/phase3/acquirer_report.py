"""Compare each absorbed system's tier with its acquirer's, where the acquirer is also in the list.

Decision 2026-10-02: an acquired/merged system's tier reflects the acquirer's pharmacy *if it serves
these hospitals*. Reviewers often could not confirm service, so tiers diverge; this report lists them
for Nate rather than changing anything.

Output: outputs/phase3_acquirer_consistency.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT  # noqa: E402
from evidence_structured import tokens  # noqa: E402


def main() -> None:
    df = pd.concat([pd.read_csv(OUT / f"phase3_{t}_classification.csv") for t in ("pilot", "full")], ignore_index=True)
    from acquirers import resolve
    fp = pd.concat([pd.read_csv(OUT / f"phase3_{t}_systems.csv") for t in ("pilot", "full")])
    footprints = {r.system_id: set(r.footprint_states.split(";")) | {r.hq_state} for r in fp.itertuples()}
    rows = []
    for sid, hits in resolve(df, footprints).items():
        r = df[df.system_id == sid].iloc[0]
        for aid in hits:
            a = df[df.system_id == aid].iloc[0]
            rows.append({"system_id": sid, "system_name": r.system_name, "status": r.status_since_2023,
                         "current_parent": r.current_parent, "tier": r.tier, "confidence": r.confidence,
                         "acquirer_id": aid, "acquirer_name": a.system_name, "acquirer_tier": a.tier,
                         "acquirer_confidence": a.confidence, "tiers_match": r.tier == a.tier,
                         "tier_source": r.tier_source})
    out = pd.DataFrame(rows).drop_duplicates(["system_id", "acquirer_id"])
    out.to_csv(OUT / "phase3_acquirer_consistency.csv", index=False)
    print(f"{len(out)} absorbed-into-listed pairs; {(~out.tiers_match).sum()} with different tiers")
    print(out[~out.tiers_match][["system_name", "tier", "acquirer_name", "acquirer_tier"]].to_string(index=False))


if __name__ == "__main__":
    main()
