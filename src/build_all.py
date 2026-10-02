"""Run Phase 1 and Phase 2, then write the combined one-row-per-system file for the Sheets load."""
import pandas as pd

import build_revenue
import build_systems
from common import OUT

REVENUE_COLS = ["system_id", "npr_compendium", "npr_compendium_basis", "n_acute_no_cost_report_compendium",
                "npr_fy2024_rebuild", "npr_fy2024_basis", "n_acute_no_cost_report_fy2024", "n_acute_annualized_fy2024",
                "gap_pct_fy2024_vs_compendium", "flag_revenue_missing", "flag_incomplete_cost_reports",
                "flag_gap_gt_25pct", "flag_hospital_value_outlier", "source_url_fy2024", "source_as_of_fy2024"]


def main() -> None:
    build_systems.main()
    build_revenue.main()
    systems = pd.read_csv(OUT / "nonprofit_systems.csv")
    revenue = pd.read_csv(OUT / "nonprofit_system_revenue.csv", usecols=REVENUE_COLS)
    combined = systems.merge(revenue, on="system_id", how="left", validate="one_to_one")
    assert len(combined) == len(systems)
    combined.to_csv(OUT / "nonprofit_systems_combined.csv", index=False)
    print(f"combined: {len(combined)} rows x {combined.shape[1]} cols")


if __name__ == "__main__":
    main()
