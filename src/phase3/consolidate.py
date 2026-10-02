"""Merge Phase 3 reviewer results into one classification file and enforce the tier rules.

Rule checks (violations are fixed down, never up, and logged in rule_adjustments):
  - tier must be one of TIERS; confidence one of High/Medium/Low.
  - a call resting only on NPPES (no accreditation, no system web page) is capped at Low.
  - "None found" requires that the system's website was searched; otherwise it becomes "Unknown".
  - Owned/Managed tiers need at least one evidence URL; otherwise "Unknown".
Also flags (does not change) URAC certificates whose roster expiration is on or before the check date,
since the roster predates the check and renewals are not visible in it.
"""
import argparse
import glob
import json
import sys
from pathlib import Path

import re
from datetime import date

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, RAW  # noqa: E402

TIERS = ["Owned, accredited", "Owned, not accredited", "Managed or partnered",
         "Infusion or home infusion only", "None found", "Unknown"]
CONF = ["High", "Medium", "Low"]
LIST_COLS = ["pharmacy_names", "accreditations", "evidence_urls", "confirmed_candidates", "rejected_candidates", "sources_searched"]


def check(r: dict) -> dict:
    notes = []
    tier, conf = r.get("tier"), r.get("confidence")
    if tier not in TIERS:
        notes.append(f"tier '{tier}' not allowed -> Unknown")
        tier = "Unknown"
    if conf not in CONF:
        notes.append(f"confidence '{conf}' not allowed -> Low")
        conf = "Low"
    src = (r.get("tier_source") or "").lower()
    web_used = any(w in src for w in ("website", "web", "press", "site", "news"))
    if tier not in ("None found", "Unknown") and not r.get("accreditations") and not web_used and "nppes" in src and conf != "Low":
        notes.append("NPPES-only evidence -> confidence capped at Low")
        conf = "Low"
    searched = " ".join(r.get("sources_searched") or []).lower()
    if tier == "None found" and not re.search(r"website|homepage|\bsite\b|pharmacy page|press release|https?://|\.(org|com|net|health|edu|gov)\b", searched):
        notes.append("None found without a recorded website search -> Unknown")
        tier = "Unknown"
    if tier.startswith(("Owned", "Managed")) and not r.get("evidence_urls"):
        notes.append("no evidence URL -> Unknown")
        tier = "Unknown"
    return {**r, "tier": tier, "confidence": conf, "rule_adjustments": "; ".join(notes)}


def urac_expiring(df: pd.DataFrame, as_of: date) -> pd.Series:
    from evidence_structured import load_urac
    exp = load_urac().set_index("urac_cert").expiration_date
    exp = pd.to_datetime(exp, errors="coerce")

    def flag(acc):
        out = [f"{c} expires {exp[c]:%Y-%m-%d}" for c in re.findall(r"SP[PS]\d{6}|IPP\d{6}", acc or "")
               if c in exp.index and pd.notna(exp[c]) and exp[c].date() <= as_of]
        return "; ".join(out)
    return df.accreditations.map(flag)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--results", default=str(RAW / "phase3_packets" / "group_*_result.json"))
    args = ap.parse_args()

    rows = []
    for f in sorted(glob.glob(args.results)):
        rows += [check(r) for r in json.loads(Path(f).read_text(encoding="utf-8"))]
    df = pd.DataFrame(rows)
    for c in LIST_COLS:
        df[c] = df[c].map(lambda v: " | ".join(map(str, v)) if isinstance(v, list) else (v or ""))
    systems = pd.read_csv(OUT / f"phase3_{args.tag}_systems.csv")[["system_id", "hq_state", "size_band", "total_beds"]]
    df = systems.merge(df, on="system_id", how="left", validate="one_to_one")
    missing = df.tier.isna().sum()
    df["tier"] = df.tier.fillna("Unknown")
    cols = ["system_id", "system_name", "hq_state", "size_band", "total_beds", "tier", "confidence", "tier_source",
            "pharmacy_names", "owning_entity", "accreditations", "manager_partner", "evidence_urls", "evidence_date",
            "confirmed_candidates", "rejected_candidates", "sources_searched", "notes", "rule_adjustments"]
    df["accreditation_expiry_check"] = urac_expiring(df, date.today())
    df = df[cols + ["accreditation_expiry_check"]]
    df.to_csv(OUT / f"phase3_{args.tag}_classification.csv", index=False)

    lines = [f"# Phase 3 {args.tag} classification ({len(df)} systems)", "",
             f"Systems with no reviewer result: {missing}. Rule adjustments: {(df.rule_adjustments.fillna('') != '').sum()}. "
             f"URAC certificates past roster expiry (renewal unverified): {', '.join(df.loc[df.accreditation_expiry_check != '', 'system_name'])}.", "",
             "| Tier | Systems |", "|---|---|", *[f"| {t} | {(df.tier == t).sum()} |" for t in TIERS], "",
             "| System | HQ | Size | Tier | Conf. | Partner | Source | Notes |", "|---|---|---|---|---|---|---|---|",
             *[f"| {r.system_name} | {r.hq_state} | {r.size_band} | {r.tier} | {r.confidence} | {r.manager_partner or ''} | "
               f"{r.tier_source or ''} | {(r.notes or '')} {('**' + r.rule_adjustments + '**') if r.rule_adjustments else ''} |"
               for r in df.fillna("").itertuples()]]
    (OUT / f"phase3_{args.tag}_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
