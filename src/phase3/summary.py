"""Write outputs/phase3_summary.md: tier counts, status changes, exclusions and the review list."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import OUT  # noqa: E402

TIERS = ["Owned, accredited", "Managed or partnered", "Owned, not accredited", "Infusion or home infusion only",
         "None found", "Unknown"]


def main() -> None:
    f = pd.read_csv(OUT / "final_nonprofit_systems.csv")
    x = pd.read_csv(OUT / "excluded_now_for_profit.csv")
    acq = pd.read_csv(OUT / "phase3_acquirer_consistency.csv")
    ct = pd.crosstab(f.sp_tier, f.sp_confidence).reindex(TIERS).fillna(0).astype(int)
    changed = f[f.status_since_2023 != "unchanged"].sort_values(["status_since_2023", "system_name"])
    review = f[(f.sp_confidence == "Low") | (f.sp_tier == "Unknown")].sort_values(["sp_tier", "system_name"])
    L = ["# Phase 3 summary: specialty pharmacy by non-profit health system", "",
         f"Systems in deliverable: **{len(f)}** (480 AHRQ non-profit systems minus {len(x)} now for-profit). "
         f"Evidence as of 2026-10-02; URAC roster 2026-09-23; Shields partner list 2026-10-02.", "",
         "## Tiers by confidence", "", "| Tier | Total | High | Medium | Low |", "|---|---|---|---|---|",
         *[f"| {t} | {ct.loc[t].sum()} | {ct.loc[t].get('High', 0)} | {ct.loc[t].get('Medium', 0)} | {ct.loc[t].get('Low', 0)} |" for t in TIERS],
         "", "## Excluded: now for-profit", "", "| System | Owner | Date |", "|---|---|---|",
         *[f"| {r.system_name} | {r.current_parent} | {r.status_change_date} |" for r in x.itertuples()],
         "", f"## Status changed since 2023 ({len(changed)})", "", "| System | Status | Now | Parent | Date |", "|---|---|---|---|---|",
         *[f"| {r.system_name} | {r.status_since_2023} | {r.current_name if isinstance(r.current_name, str) else ''} | "
           f"{r.current_parent if isinstance(r.current_parent, str) else ''} | {r.status_change_date if isinstance(r.status_change_date, str) else ''} |"
           for r in changed.itertuples()],
         "", f"## For review: acquired systems whose tier differs from their listed acquirer ({(~acq.tiers_match).sum()})", "",
         "| System | Tier | Acquirer | Acquirer tier |", "|---|---|---|---|",
         *[f"| {r.system_name} | {r.tier} | {r.acquirer_name} | {r.acquirer_tier} |" for r in acq[~acq.tiers_match].itertuples()],
         "", f"## For review: Low confidence or Unknown ({len(review)})", "",
         "| System | HQ | Tier | Notes |", "|---|---|---|---|",
         *[f"| {r.system_name} | {r.hq_state} | {r.sp_tier} | {str(r.sp_notes)[:160] if isinstance(r.sp_notes, str) else ''} |" for r in review.itertuples()]]
    (OUT / "phase3_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:16]))


if __name__ == "__main__":
    main()
