# US non-profit health systems research

Public data only. Builds a list of US non-profit health systems (AHRQ definition) by HQ state, with hospital net patient revenue. Phase 3 (specialty pharmacy classification) comes next.

## Run

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python src/fetch_data.py   # raw files -> data/raw (gitignored)
.venv/Scripts/python src/build_all.py    # outputs/*.csv + QA reports
```

If AHRQ answers with a WAF challenge, `fetch_data.py` stops and names the file. Download it in a browser into `data/raw/`.

## Outputs

| File | Grain | Content |
|---|---|---|
| `outputs/nonprofit_systems_combined.csv` | system (480) | Phase 1 + Phase 2 columns; the Sheets load file |
| `outputs/nonprofit_systems.csv` | system | Phase 1: HQ, footprint, counts, beds, DSH, ownership |
| `outputs/nonprofit_member_hospitals.csv` | hospital (2,977) | Phase 1 audit trail |
| `outputs/nonprofit_system_revenue.csv` | system | Phase 2: Compendium NPR, FY2024 rebuild, flags |
| `outputs/nonprofit_member_hospital_revenue.csv` | acute hospital (2,697) | Phase 2 audit trail |
| `outputs/qa_phase1.md`, `qa_phase1_spotcheck.md`, `qa_phase2.md` | | QA results |

## Key definitions

- **Universe:** AHRQ Compendium 2023 systems whose `sys_ownership` is 1 (nonprofit) or 2 (church-operated), plus University of Miami Health System (code missing; nonprofit per HCRIS). Ownership is assigned by majority of acute beds; `mixed_ownership` and `pct_nonprofit_acute_beds` show exceptions.
- **hq_state:** AHRQ home-office state. `footprint_states` = every state with a member hospital (any type).
- **total_beds:** AHRQ `sys_beds` = beds in non-federal general acute member hospitals (HCRIS).
- **npr_compendium:** sum of net patient revenue (HCRIS Worksheet G-3, line 3) across non-federal general acute member hospitals; HCRIS FY2023 with FY2022 fallback. Covers hospitals only, excluding physician groups and other lines. Understated when a member has no cost report; see `n_acute_no_cost_report_compendium`.
- **npr_fy2024_rebuild:** the same sum from CMS HCRIS FY2024 (cost reports beginning 2023-10-01 to 2024-09-30). Multiple or short reports per CCN are annualized as sum(NPR) / days × 365.
- Source values are never corrected. Suspected cost-report errors (negative NPR, or a 0.5–2× swing between years) are flagged, not fixed. Unknown stays blank, never zero.

Phase 0 verification and source notes are in `docs/phase0_findings.md`.
