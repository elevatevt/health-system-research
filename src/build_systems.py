"""Phase 1: non-profit health systems by HQ state, plus a member-hospital audit trail.

Outputs:
  outputs/nonprofit_systems.csv         one row per system
  outputs/nonprofit_member_hospitals.csv one row per member hospital
  outputs/qa_phase1.md
"""
import pandas as pd

from common import (COMPENDIUM_EDITION, NONPROFIT_CODES, OUT, OWNERSHIP, SOURCES,
                    load_hospitals, load_systems, nonprofit_system_ids)


def ownership_mix(acute: pd.DataFrame) -> pd.DataFrame:
    """Share of acute beds in nonprofit/church hospitals, among beds with an HCRIS ownership code."""
    known = acute.dropna(subset=["hos_ownership", "hos_beds"])
    np_beds = known[known.hos_ownership.isin(NONPROFIT_CODES)].groupby("health_sys_id").hos_beds.sum()
    all_beds = known.groupby("health_sys_id").hos_beds.sum()
    other = acute[acute.hos_ownership.isin({3, 4, 5})].groupby("health_sys_id").size()
    return pd.DataFrame({
        "pct_nonprofit_acute_beds": (np_beds.reindex(all_beds.index, fill_value=0) / all_beds * 100).round(1),
        "n_acute_non_nonprofit": other,
    })


def main() -> None:
    systems, hospitals = load_systems(), load_hospitals()
    ids = nonprofit_system_ids(systems)
    sys_np = systems[systems.health_sys_id.isin(ids)].copy()
    hosp_np = hospitals[hospitals.health_sys_id.isin(ids)].copy()
    acute = hosp_np[hosp_np.acutehosp_flag == 1]

    footprint = hosp_np.groupby("health_sys_id").hospital_state.agg(lambda s: ";".join(sorted(set(s.dropna()))))
    mix = ownership_mix(acute)

    out = pd.DataFrame({
        "system_id": sys_np.health_sys_id,
        "system_name": sys_np.health_sys_name,
        "hq_city": sys_np.health_sys_city,
        "hq_state": sys_np.health_sys_state,
        "footprint_states": sys_np.health_sys_id.map(footprint),
        "n_footprint_states": sys_np.health_sys_id.map(footprint).str.count(";") + 1,
        "hq_state_in_footprint": [hq in fp.split(";") for hq, fp in zip(sys_np.health_sys_state, sys_np.health_sys_id.map(footprint))],
        "n_hospitals": sys_np.hosp_cnt,
        "n_acute_hospitals": sys_np.acutehosp_cnt,
        "total_beds": sys_np.sys_beds,  # AHRQ: beds in non-federal general acute care hospitals (HCRIS)
        "any_high_dsh_hospital": sys_np.sys_incl_highdpphosp,
        "ownership_code": sys_np.sys_ownership.astype("Int64"),
        "ownership_label": sys_np.sys_ownership.map(OWNERSHIP).fillna("missing in AHRQ; nonprofit per member-hospital HCRIS"),
        "pct_nonprofit_acute_beds": sys_np.health_sys_id.map(mix.pct_nonprofit_acute_beds),
        "n_acute_non_nonprofit": sys_np.health_sys_id.map(mix.n_acute_non_nonprofit).fillna(0).astype(int),
        "compendium_edition": COMPENDIUM_EDITION,
        "source_url": SOURCES["compendium_systems"]["url"],
        "source_as_of": SOURCES["compendium_systems"]["as_of"],
    })
    out["mixed_ownership"] = out.n_acute_non_nonprofit > 0
    out = out.sort_values(["hq_state", "system_name"]).reset_index(drop=True)

    members = pd.DataFrame({
        "ccn": hosp_np.ccn,
        "compendium_hospital_id": hosp_np.compendium_hospital_id,
        "hospital_name": hosp_np.hospital_name,
        "hospital_city": hosp_np.hospital_city,
        "hospital_state": hosp_np.hospital_state,
        "system_id": hosp_np.health_sys_id,
        "system_name": hosp_np.health_sys_name,
        "acute_flag": hosp_np.acutehosp_flag,
        "ownership_code": hosp_np.hos_ownership.astype("Int64"),
        "ownership_label": hosp_np.hos_ownership.map(OWNERSHIP),
        "beds": hosp_np.hos_beds.astype("Int64"),
        "high_dsh_flag": hosp_np.hos_highdpp.astype("Int64"),
        "source_url": SOURCES["compendium_hospitals"]["url"],
    }).sort_values(["system_id", "hospital_state", "hospital_name"])

    OUT.mkdir(exist_ok=True)
    out.to_csv(OUT / "nonprofit_systems.csv", index=False)
    members.to_csv(OUT / "nonprofit_member_hospitals.csv", index=False)
    write_qa(out, members, hosp_np)


def write_qa(out: pd.DataFrame, members: pd.DataFrame, hosp_np: pd.DataFrame) -> None:
    checks = []

    def check(name, ok, detail=""):
        checks.append(f"- [{'PASS' if ok else 'FAIL'}] {name}{': ' + detail if detail else ''}")

    check("every system has >=1 acute hospital", (out.n_acute_hospitals >= 1).all(),
          f"min {out.n_acute_hospitals.min()}")
    check("member acute count equals AHRQ acutehosp_cnt",
          (members.groupby("system_id").acute_flag.sum().reindex(out.system_id).values == out.n_acute_hospitals.values).all())
    check("member count equals AHRQ hosp_cnt",
          (members.groupby("system_id").size().reindex(out.system_id).values == out.n_hospitals.values).all())
    pairs_out = out.footprint_states.str.split(";").explode()
    pairs_file = hosp_np.groupby("health_sys_id").hospital_state.nunique().sum()
    check("footprint (system,state) pairs reconcile to hospital file", len(pairs_out) == pairs_file,
          f"{len(pairs_out)} vs {pairs_file}")
    check("system_id unique", out.system_id.is_unique)

    lines = [
        "# Phase 1 QA", "",
        f"Systems: **{len(out)}** (nonprofit {(out.ownership_code == 1).sum()}, church-operated {(out.ownership_code == 2).sum()}, "
        f"missing code {out.ownership_code.isna().sum()}). Member hospitals: {len(members)} ({members.acute_flag.sum()} acute).", "",
        *checks, "",
        f"Mixed ownership (>=1 acute hospital coded public/for-profit/other): **{out.mixed_ownership.sum()}** systems.",
        f"HQ state not in hospital footprint: {', '.join(out.loc[~out.hq_state_in_footprint, 'system_name'] + ' (' + out.loc[~out.hq_state_in_footprint, 'hq_state'] + ')')}.",
        f"Multi-state systems: {(out.n_footprint_states > 1).sum()}.", "",
        "## Systems by HQ state", "",
        "| State | Systems |", "|---|---|",
        *[f"| {s} | {n} |" for s, n in out.hq_state.value_counts().sort_index().items()],
    ]
    (OUT / "qa_phase1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
