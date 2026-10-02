"""Phase 2: net patient revenue per non-profit system.

Primary: AHRQ Compendium system net patient revenue (HCRIS FY2023, FY2022 fallback;
non-federal general acute care member hospitals only).
Secondary: rebuilt from CMS HCRIS FY2024 by summing the same acute member CCNs.

HCRIS Worksheet G-3 line 3 col 1 ("Net Patient Revenue") = gross patient revenue less
contractual allowances and discounts. Hospital operations only: no physician groups or
other business lines.

FY2024 = cost reports *beginning* 2023-10-01..2024-09-30. A CCN with several reports
(fiscal-year change, change of ownership) or a short period is annualized:
sum(NPR) / sum(days) * 365.

Outputs:
  outputs/nonprofit_system_revenue.csv
  outputs/nonprofit_member_hospital_revenue.csv
  outputs/qa_phase2.md
"""
import pandas as pd

from common import OUT, SOURCES, load_hospitals, load_systems, nonprofit_system_ids, raw

GAP_THRESHOLD = 0.25
SHORT_DAYS = 300
# A member hospital whose FY2024/Compendium ratio falls outside this band, or whose NPR is
# negative in either source, is flagged as a likely cost-report data error. Values are not corrected.
RATIO_BAND = (0.5, 2.0)


def hcris_annualized(path) -> pd.DataFrame:
    cols = ["Provider CCN", "Fiscal Year Begin Date", "Fiscal Year End Date", "Net Patient Revenue"]
    c = pd.read_csv(path, usecols=cols, dtype={"Provider CCN": str},
                    parse_dates=["Fiscal Year Begin Date", "Fiscal Year End Date"])
    c["ccn"] = c["Provider CCN"].str.zfill(6)
    c = c.dropna(subset=["Net Patient Revenue"])
    c["days"] = (c["Fiscal Year End Date"] - c["Fiscal Year Begin Date"]).dt.days + 1
    g = c.groupby("ccn").agg(npr_sum=("Net Patient Revenue", "sum"), days=("days", "sum"),
                             n_reports=("days", "size"),
                             fy_begin=("Fiscal Year Begin Date", "min"), fy_end=("Fiscal Year End Date", "max"))
    g["npr_fy2024"] = g.npr_sum / g.days * 365
    g["annualized"] = (g.n_reports > 1) | ((g.days - 365).abs() > 5)
    return g


def main() -> None:
    systems, hospitals = load_systems(), load_hospitals()
    ids = nonprofit_system_ids(systems)
    sys_np = systems[systems.health_sys_id.isin(ids)].set_index("health_sys_id")
    acute = hospitals[hospitals.health_sys_id.isin(ids) & (hospitals.acutehosp_flag == 1)].copy()

    h24 = hcris_annualized(raw("hcris_fy2024"))
    acute = acute.join(h24[["npr_fy2024", "days", "n_reports", "annualized", "fy_begin", "fy_end"]], on="ccn")

    ratio = acute.npr_fy2024 / acute.hos_net_revenue
    acute["negative_npr"] = (acute.hos_net_revenue < 0) | (acute.npr_fy2024 < 0)
    acute["value_outlier"] = acute.negative_npr | (ratio < RATIO_BAND[0]) | (ratio > RATIO_BAND[1])

    by_sys = acute.groupby("health_sys_id")
    out = pd.DataFrame({
        "system_name": sys_np.health_sys_name,
        "hq_state": sys_np.health_sys_state,
        "n_acute_hospitals": sys_np.acutehosp_cnt,
        "npr_compendium": sys_np.hos_net_revenue,
        "npr_compendium_basis": "HCRIS FY2023 (FY2022 fallback); acute member hospitals; G-3 line 3",
        "n_acute_no_cost_report_compendium": by_sys.hos_net_revenue.apply(lambda s: s.isna().sum()),
        "npr_fy2024_rebuild": by_sys.npr_fy2024.sum(min_count=1).round(0),
        "npr_fy2024_basis": "HCRIS FY2024 (periods beginning 2023-10-01..2024-09-30); acute member CCNs; annualized where needed",
        "n_acute_no_cost_report_fy2024": by_sys.npr_fy2024.apply(lambda s: s.isna().sum()),
        "n_acute_annualized_fy2024": by_sys.annualized.apply(lambda s: int(s.fillna(False).sum())),
    })
    out["gap_pct_fy2024_vs_compendium"] = ((out.npr_fy2024_rebuild / out.npr_compendium - 1) * 100).round(1)
    out["flag_revenue_missing"] = out.npr_compendium.isna()
    out["flag_incomplete_cost_reports"] = (out.n_acute_no_cost_report_compendium > 0) | (out.n_acute_no_cost_report_fy2024 > 0)
    out["flag_gap_gt_25pct"] = out.gap_pct_fy2024_vs_compendium.abs() > GAP_THRESHOLD * 100
    out["flag_hospital_value_outlier"] = by_sys.value_outlier.any()
    out["coverage_differs"] = out.n_acute_no_cost_report_compendium != out.n_acute_no_cost_report_fy2024
    out["source_url_compendium"] = SOURCES["compendium_systems"]["url"]
    out["source_url_fy2024"] = SOURCES["hcris_fy2024"]["url"]
    out["source_as_of_fy2024"] = SOURCES["hcris_fy2024"]["as_of"]
    out = out.rename_axis("system_id").reset_index().sort_values(["hq_state", "system_name"])

    members = pd.DataFrame({
        "ccn": acute.ccn, "hospital_name": acute.hospital_name, "hospital_state": acute.hospital_state,
        "system_id": acute.health_sys_id,
        "npr_compendium": acute.hos_net_revenue,
        "npr_fy2024": acute.npr_fy2024.round(0),
        "fy2024_reports": acute.n_reports.astype("Int64"),
        "fy2024_days": acute.days.astype("Int64"),
        "fy2024_period": acute.fy_begin.dt.strftime("%Y-%m-%d") + ".." + acute.fy_end.dt.strftime("%Y-%m-%d"),
        "fy2024_annualized": acute.annualized,
        "flag_negative_npr": acute.negative_npr,
        "flag_value_outlier": acute.value_outlier,
    }).sort_values(["system_id", "hospital_name"])

    out.to_csv(OUT / "nonprofit_system_revenue.csv", index=False)
    members.to_csv(OUT / "nonprofit_member_hospital_revenue.csv", index=False)
    write_qa(out, members)


def write_qa(out: pd.DataFrame, members: pd.DataFrame) -> None:
    both = out.dropna(subset=["npr_compendium", "npr_fy2024_rebuild"])
    same_cov = both[~both.coverage_differs]
    big = out[out.flag_gap_gt_25pct].sort_values("gap_pct_fy2024_vs_compendium")
    short = members[members.fy2024_days < SHORT_DAYS]
    lines = [
        "# Phase 2 QA", "",
        f"Systems: {len(out)}.",
        f"- Compendium revenue missing: **{out.flag_revenue_missing.sum()}** ({', '.join(out.loc[out.flag_revenue_missing, 'system_name'])}).",
        f"- FY2024 rebuild missing (no member cost reports): {out.npr_fy2024_rebuild.isna().sum()}.",
        f"- Systems with >=1 acute member lacking a cost report: Compendium {(out.n_acute_no_cost_report_compendium > 0).sum()}, "
        f"FY2024 {(out.n_acute_no_cost_report_fy2024 > 0).sum()}, either {out.flag_incomplete_cost_reports.sum()}.",
        f"- Acute member hospitals: {len(members)}; FY2024 cost report found {members.npr_fy2024.notna().sum()} "
        f"({members.npr_fy2024.notna().mean():.1%}); annualized {int(members.fy2024_annualized.fillna(False).sum())}; "
        f"covering <{SHORT_DAYS} days {len(short)}.",
        f"- Totals where both exist ({len(both)} systems): Compendium ${both.npr_compendium.sum() / 1e9:,.1f}B, "
        f"FY2024 ${both.npr_fy2024_rebuild.sum() / 1e9:,.1f}B.",
        f"- Median FY2024 vs Compendium gap: all {both.gap_pct_fy2024_vs_compendium.median():.1f}%; "
        f"same hospital coverage ({len(same_cov)} systems) {same_cov.gap_pct_fy2024_vs_compendium.median():.1f}%.",
        f"- Member hospitals flagged as likely cost-report errors (negative NPR or FY2024/Compendium ratio outside "
        f"{RATIO_BAND[0]}-{RATIO_BAND[1]}x): {int(members.flag_value_outlier.sum())} in {int(out.flag_hospital_value_outlier.sum())} systems "
        f"({int(members.flag_negative_npr.sum())} negative). Source values are kept as published.",
        f"- **Gap >25%: {len(big)} systems** ({big.coverage_differs.sum()} of them have different hospital coverage between the two years).",
        "", "## Hospital-level outliers", "",
        "| Hospital | State | System | Compendium $M | FY2024 $M |", "|---|---|---|---|---|",
        *[f"| {r.hospital_name} | {r.hospital_state} | {r.system_id} | {r.npr_compendium / 1e6:,.0f} | {r.npr_fy2024 / 1e6:,.0f} |"
          for r in members[members.flag_value_outlier].itertuples()],
        "", "## Systems with >25% gap", "",
        "| System | HQ | Compendium $M | FY2024 $M | Gap % | Missing CR (Comp/FY24) | Hospital outlier |", "|---|---|---|---|---|---|---|",
        *[f"| {r.system_name} | {r.hq_state} | {r.npr_compendium / 1e6:,.0f} | {r.npr_fy2024_rebuild / 1e6:,.0f} | "
          f"{r.gap_pct_fy2024_vs_compendium:+.1f} | {r.n_acute_no_cost_report_compendium}/{r.n_acute_no_cost_report_fy2024} | {'yes' if r.flag_hospital_value_outlier else ''} |"
          for r in big.itertuples()],
    ]
    (OUT / "qa_phase2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
