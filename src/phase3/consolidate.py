"""Merge Phase 3 reviewer results into one classification file and enforce the tier rules.

Rule checks (violations are fixed down, never up, and logged in rule_adjustments):
  - tier must be one of TIERS; confidence one of High/Medium/Low.
  - a call resting only on NPPES (no accreditation, no system web page) is capped at Low.
  - "None found" requires that the system's website was searched; otherwise it becomes "Unknown".
  - Owned/Managed tiers need at least one evidence URL; otherwise "Unknown".
  - status "closed": tier and confidence are blank (decision 2026-10-02).
  - a status with no status_evidence_url becomes "unverified" (a status sweep re-checks these).
  - Shields partner list (decision 2026-10-02): a system on the list is "Managed or partnered" by
    Shields Health Solutions. Matched on distinctive name tokens plus a footprint state.
Also notes URAC certificates past their roster expiration date; per decision 2026-10-02 they are
treated as current unless a lapse is found.
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
from evidence_structured import tokens  # noqa: E402

SHIELDS_FILE = RAW / "shields_partners_20261002.txt"
SHIELDS_URL = "https://shieldshealthsolutions.com/about-us/partner-health-systems"
STATUS_COLS = ["current_name", "status_since_2023", "current_parent", "status_evidence_url", "status_change_date", "now_for_profit"]
# Backstop for now_for_profit (decision 2026-10-02: systems now for-profit are excluded from the deliverable).
FOR_PROFIT_PARENTS = ["hca", "tenet", "community health systems", "lifepoint", "universal health services", "ardent",
                      "prime healthcare", "scionhealth", "steward", "quorum", "envision", "surgery partners"]

TIERS = ["Owned, accredited", "Owned, not accredited", "Managed or partnered",
         "Infusion or home infusion only", "None found", "Unknown"]
CONF = ["High", "Medium", "Low"]
LIST_COLS = ["pharmacy_names", "accreditations", "evidence_urls", "confirmed_candidates", "rejected_candidates", "sources_searched"]


def check(r: dict) -> dict:
    notes = []
    tier, conf = r.get("tier"), r.get("confidence")
    parent = (r.get("current_parent") or "").lower()
    fp = str(r.get("now_for_profit", "")).lower() == "true" or any(n in parent for n in FOR_PROFIT_PARENTS)
    if fp:
        if str(r.get("now_for_profit", "")).lower() != "true":
            notes.append(f"current parent '{r.get('current_parent')}' is for-profit -> now_for_profit")
        return {**r, "now_for_profit": True, "tier": "", "confidence": "", "rule_adjustments": "; ".join(notes)}
    r = {**r, "now_for_profit": False}
    status = (r.get("status_since_2023") or "").strip()
    if status and not r.get("status_evidence_url"):
        notes.append(f"status '{status}' has no evidence URL -> unverified")
        r = {**r, "status_since_2023": "unverified"}
    if status.lower() == "closed" and r["status_since_2023"] == "closed":
        return {**r, "tier": "", "confidence": "", "rule_adjustments": "; ".join(notes)}
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


def load_shields() -> pd.DataFrame:
    rows = []
    for line in SHIELDS_FILE.read_text(encoding="utf-8").splitlines()[1:]:
        name, loc = line.split("\t")
        rows.append({"shields_name": name.rstrip("*").strip(), "state": loc.rsplit(",", 1)[-1].strip()})
    s = pd.DataFrame(rows)
    s["tok"] = s.shields_name.map(tokens)
    return s


def shields_match(name_tokens: frozenset, states: set, shields: pd.DataFrame) -> str:
    if not name_tokens:
        return ""
    ok = shields.state.isin(states) & shields.tok.map(lambda t: bool(t) and (t <= name_tokens or name_tokens <= t))
    hit = shields[ok]
    return "; ".join(sorted(set(hit.shields_name + " (" + hit.state + ")")))


def apply_shields(df: pd.DataFrame, systems: pd.DataFrame) -> pd.DataFrame:
    shields = load_shields()
    fp = systems.set_index("system_id").footprint_states.str.split(";").map(set)
    df["shields_list_match"] = [
        shields_match(tokens(r.system_name) | tokens(r.current_name), fp.get(r.system_id, set()) | {r.hq_state}, shields)
        for r in df.fillna("").itertuples()]
    on_list = (df.shields_list_match != "") & (df.tier != "") & df.reviewed
    change = on_list & (df.tier != "Managed or partnered")
    df.loc[change, "rule_adjustments"] = (df.loc[change, "rule_adjustments"].fillna("") + "; on Shields partner list: "
                                          + df.loc[change, "tier"] + " -> Managed or partnered").str.lstrip("; ")
    df.loc[change & df.confidence.isin(["Low", ""]), "confidence"] = "Medium"
    df.loc[on_list, "tier"] = "Managed or partnered"
    df.loc[on_list, "manager_partner"] = "Shields Health Solutions"
    df.loc[on_list, "evidence_urls"] = df.loc[on_list, "evidence_urls"].fillna("").map(
        lambda u: u if SHIELDS_URL in u else (u + " | " + SHIELDS_URL).strip(" |"))
    return df


def urac_expiring(df: pd.DataFrame, as_of: date) -> pd.Series:
    from evidence_structured import load_urac
    exp = load_urac().set_index("urac_cert").expiration_date
    exp = pd.to_datetime(exp, errors="coerce")

    def flag(acc):
        out = [f"{c} expires {exp[c]:%Y-%m-%d}" for c in re.findall(r"SP[PS]\d{6}|IPP\d{6}", acc if isinstance(acc, str) else "")
               if c in exp.index and pd.notna(exp[c]) and exp[c].date() <= as_of]
        return "; ".join(out)
    return df.accreditations.map(flag)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--results", help="glob of reviewer result files (default by tag)")
    ap.add_argument("--overrides", help="glob of result files whose fields replace earlier ones (e.g. a refresh)")
    args = ap.parse_args()
    default = {"pilot": RAW / "phase3_packets" / "group_*_result.json", "full": RAW / "phase3_full" / "group_*_result.json"}
    results = args.results or str(default[args.tag])
    overrides = args.overrides or str({"pilot": RAW / "phase3_packets" / "pilot_refresh_result.json",
                                       "full": RAW / "phase3_full" / "status_sweep_*.json"}[args.tag])

    by_id = {}
    for pattern in [results] + ([overrides] if overrides else []):
        for f in sorted(glob.glob(pattern)):
            for r in json.loads(Path(f).read_text(encoding="utf-8")):
                by_id[r["system_id"]] = {**by_id.get(r["system_id"], {}), **r}
    df = pd.DataFrame([check(r) for r in by_id.values()])
    for c in STATUS_COLS:
        if c not in df:
            df[c] = ""
    for c in LIST_COLS:
        df[c] = df[c].map(lambda v: " | ".join(map(str, v)) if isinstance(v, list) else (v or ""))
    systems = pd.read_csv(OUT / f"phase3_{args.tag}_systems.csv")
    df = systems[["system_id", "hq_state", "total_beds"]].merge(df, on="system_id", how="left", validate="one_to_one")
    df["reviewed"] = df.tier.notna()
    missing = (~df.reviewed).sum()
    df["system_name"] = df.system_name.fillna(df.system_id.map(systems.set_index("system_id").system_name))
    df["tier"] = df.tier.fillna("Unknown")
    df = apply_shields(df, systems)
    cols = ["system_id", "system_name", "hq_state", "total_beds", *STATUS_COLS, "tier", "confidence", "tier_source",
            "pharmacy_names", "owning_entity", "accreditations", "manager_partner", "evidence_urls", "evidence_date",
            "confirmed_candidates", "rejected_candidates", "sources_searched", "notes", "shields_list_match", "rule_adjustments"]
    df["accreditation_expiry_check"] = urac_expiring(df, date.today())
    df = df[cols + ["accreditation_expiry_check"]]
    df.to_csv(OUT / f"phase3_{args.tag}_classification.csv", index=False)

    lines = [f"# Phase 3 {args.tag} classification ({len(df)} systems)", "",
             f"Systems with no reviewer result: {missing}. Rule adjustments: {(df.rule_adjustments.fillna('') != '').sum()}. "
             f"URAC certificates past roster expiry (treated as current): {(df.accreditation_expiry_check != '').sum()}.", "",
             "| Tier | Systems |", "|---|---|", *[f"| {t} | {(df.tier == t).sum()} |" for t in TIERS],
             f"| (closed, no tier) | {(df.status_since_2023.fillna('').str.lower() == 'closed').sum()} |",
             f"| (now for-profit, excluded) | {(df.now_for_profit == True).sum()} |", "",
             "| System | HQ | Status | Tier | Conf. | Partner | Source | Notes |", "|---|---|---|---|---|---|---|---|",
             *[f"| {r.system_name} | {r.hq_state} | {r.status_since_2023} {('-> ' + r.current_name) if r.current_name and r.current_name != r.system_name else ''} | {r.tier} | {r.confidence} | {r.manager_partner or ''} | "
               f"{r.tier_source or ''} | {(r.notes or '')} {('**' + r.rule_adjustments + '**') if r.rule_adjustments else ''} |"
               for r in df.fillna("").itertuples()]]
    (OUT / f"phase3_{args.tag}_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
