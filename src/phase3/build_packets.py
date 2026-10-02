"""Write reviewer packets (5 systems each) for a Phase 3 run from its candidate files.

  python src/phase3/build_packets.py --tag full   -> data/raw/phase3_full/group_NNN.json
Systems are ordered as in outputs/phase3_<tag>_systems.csv.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import OUT, RAW, load_hospitals  # noqa: E402

KEEP = {"urac": ["urac_cert", "program", "status", "organization", "street", "city", "state", "effective_date",
                 "expiration_date", "evidence_url", "match_basis"],
        "achc": ["achc_list", "achc_company_id", "organization", "dba", "street", "city", "state", "evidence_url", "match_basis"],
        "nppes": ["npi", "org_name", "other_names", "specialty_is_primary", "primary_taxonomy", "street", "city", "state",
                  "authorized_official_title", "last_updated", "evidence_url", "match_basis"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="full")
    ap.add_argument("--size", type=int, default=5)
    args = ap.parse_args()
    systems = pd.read_csv(OUT / f"phase3_{args.tag}_systems.csv")
    cand = {k: pd.read_csv(OUT / f"phase3_{args.tag}_{k}_candidates.csv", dtype=str) for k in KEEP}
    hospitals = load_hospitals()
    out_dir = RAW / f"phase3_{args.tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for g, start in enumerate(range(0, len(systems), args.size), 1):
        packet = []
        for r in systems.iloc[start:start + args.size].itertuples():
            m = hospitals[hospitals.health_sys_id == r.system_id]
            packet.append({
                "system_id": r.system_id, "system_name": r.system_name, "hq": f"{r.hq_city}, {r.hq_state}",
                "footprint_states": r.footprint_states, "acute_beds": r.total_beds,
                "member_hospitals": [f"{x.hospital_name} ({x.hospital_city}, {x.hospital_state})" for x in m.itertuples()][:40],
                "candidates": {k: c[c.system_id == r.system_id][KEEP[k]].fillna("").to_dict("records") for k, c in cand.items()},
            })
        (out_dir / f"group_{g:03d}.json").write_text(json.dumps(packet, indent=1), encoding="utf-8")
    print(f"{g} packets in {out_dir}")


if __name__ == "__main__":
    main()
