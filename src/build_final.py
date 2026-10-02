"""Final deliverable: Phase 1-2 system rows joined to Phase 3 specialty pharmacy calls (pilot + full run).

Systems now for-profit (acquired by or converted to a for-profit owner since 2023) are excluded,
per Nate's decision of 2026-10-02, and listed separately for audit.

Outputs:
  outputs/final_nonprofit_systems.csv   the Sheets load file
  outputs/excluded_now_for_profit.csv   excluded systems with the evidence
"""
import pandas as pd

from common import OUT

PHASE3_COLS = {
    "current_name": "current_name", "status_since_2023": "status_since_2023", "current_parent": "current_parent",
    "status_evidence_url": "status_evidence_url", "status_change_date": "status_change_date",
    "now_for_profit": "now_for_profit",
    "tier": "sp_tier", "confidence": "sp_confidence", "tier_source": "sp_tier_source",
    "pharmacy_names": "sp_pharmacy_names", "owning_entity": "sp_owning_entity", "accreditations": "sp_accreditations",
    "manager_partner": "sp_manager_partner", "evidence_urls": "sp_evidence_urls", "evidence_date": "sp_evidence_date",
    "notes": "sp_notes", "rule_adjustments": "sp_rule_adjustments",
}


def main() -> None:
    systems = pd.read_csv(OUT / "nonprofit_systems_combined.csv")
    frames = [pd.read_csv(OUT / f"phase3_{tag}_classification.csv") for tag in ("pilot", "full")
              if (OUT / f"phase3_{tag}_classification.csv").exists()]
    p3 = pd.concat(frames, ignore_index=True)
    assert p3.system_id.is_unique, "a system appears in both pilot and full results"
    p3["reviewed"] = p3.tier_source.notna() | p3.status_since_2023.notna()
    p3 = p3[["system_id", "reviewed", *PHASE3_COLS]].rename(columns=PHASE3_COLS)

    df = systems.merge(p3, on="system_id", how="left", validate="one_to_one")
    df["reviewed"] = df.reviewed.fillna(False).astype(bool)
    fp = df.now_for_profit.astype(str).str.lower() == "true"

    excluded = df[fp][["system_id", "system_name", "hq_state", "current_name", "current_parent",
                       "status_since_2023", "status_change_date", "status_evidence_url"]]
    final = df[~fp].drop(columns=["now_for_profit"])
    final.to_csv(OUT / "final_nonprofit_systems.csv", index=False)
    excluded.to_csv(OUT / "excluded_now_for_profit.csv", index=False)

    print(f"final: {len(final)} systems ({final.reviewed.sum()} with Phase 3 results); excluded now for-profit: {len(excluded)}")
    print(final.loc[final.reviewed, "sp_tier"].fillna("(closed)").replace("", "(closed)").value_counts().to_string())
    if len(excluded):
        print(excluded[["system_name", "current_parent", "status_change_date"]].to_string(index=False))


if __name__ == "__main__":
    main()
