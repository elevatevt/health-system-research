# Phase 0 findings (verified 2026-10-02 ET)

Decisions confirmed by Nate 2026-10-02: Compendium 2023 rev; universe = ownership code 1 or 2 plus University of Miami (480 systems), keeping the mixed-ownership systems with a `pct_nonprofit_acute_beds` column; revenue = Compendium net patient revenue plus an HCRIS FY2024 rebuild; no Form 990 column.

## V1 Network
All hosts are reachable from corsairone. ahrq.gov returns an empty 202 or an AWS WAF challenge page to bare scripts; downloads work with browser headers but not reliably, so `fetch_data.py` fails loudly on a challenge page. urac.org and achc.org return 403 to scripts and load in a browser.

## V2 Edition
2023 is the latest edition; the index lists 2016–2023. The system file was revised 2025-09 to add Medicare Advantage variables. It has 639 systems and 6,800 hospitals, 4,193 of them in systems.
Source: https://www.ahrq.gov/chsp/data-resources/compendium-2023.html

## V3 Ownership
`sys_ownership` = the ownership type of the majority of the system's non-federal general acute beds (HCRIS, then AHA majority, then AHA plurality). The 2023 system tech doc, Table IV.2 and Appendix F, is the source.
- Codes: 1 nonprofit, 2 church-operated, 3 public/government, 5 for-profit.
- The hospital-linkage tech doc lists 2 = public and 3 = church. That is wrong: code 2 systems are Ascension, AdventHealth, CHRISTUS and Mercy, and code-3 systems are county and authority systems.
- Hospital code 4 (15 hospitals, mostly IHS/tribal) is undocumented.
- 439 systems are code 1 and 40 are code 2. University of Miami has no code; its one HCRIS-coded hospital is code 1.
- 73 of the 480 have at least one acute hospital coded 3, 4 or 5. Two have under 50% nonprofit beds: SEARHC (tribal) and Heritage Valley.

## V4 HQ state
`health_sys_state` = the home-office state, per the 2023 page's column description. It matches the hospital file in 100% of rows. Ascension (MO), CommonSpirit (IL) and Covenant Health (MA) have no hospital in their HQ state.

## V5 Revenue definition
- `hos_net_revenue` (system) = the sum of net patient revenue across non-federal general acute member hospitals. It reproduces exactly for 634 of 639 systems; the other 5 are blank.
- HCRIS Worksheet G-3, line 3, column 1 = gross patient revenue (G-3 line 1) less contractual allowances and discounts (G-3 line 2). It covers hospital operations only.
- AHRQ's data dictionary swaps the descriptions of `hos_net_revenue` and `hos_total_revenue`. The values confirm the column names are correct.
- The vintage is HCRIS 2023, with 2022 as fallback. The data matches the data.cms.gov "2023" file: a rebuild gives a median gap of 0.1%. That file is federal FY2023, covering cost reports that *begin* 2022-10-01 to 2023-09-30, not a calendar year.
- Sources:
  - CMS Hospital Cost Report Data Dictionary: https://data.cms.gov/sites/default/files/2022-12/47c231b2-3b8e-4b97-bbdd-d92e762330ff/Hospital%20Cost%20Report%20Data%20Dictionary_508.pdf
  - 2023 Compendium tech doc: https://www.ahrq.gov/sites/default/files/wysiwyg/chsp/compendium/2023-compendium-techdoc-rev.pdf

## V6 Fresher HCRIS
FY2024 (periods beginning 2023-10-01 to 2024-09-30) is on data.cms.gov, modified 2026-09-29. It has 5,825 rows, against 6,105 for FY2023, so it is still filling in. See `outputs/qa_phase2.md` for the rebuild results.

## V7 Form 990 (dropped)
The ProPublica API works, but the 990 is not a usable comparator:
- Name search is ambiguous: "Mercy Health" returns 144 organizations.
- The parent's EIN return is not consolidated. Ascension Health's 2023 Form 990 shows $228M in total revenue, against $21.9B in Compendium net patient revenue.

## V8 Phase 3 directories
- **URAC:** searchable by program and state, no export. The Terms of Use bar automated access and allow personal, non-commercial use only. Nate supplied a roster workbook pulled 2026-09-23 from a prior session; it is in `data/raw` and is not refreshed by this repo.
- **ACHC:** organization.achc.org is searchable by program (Pharmacy, Home Infusion Therapy), service and state. Its terms have no automation clause, and robots.txt allows crawling with a 10-second crawl delay on achc.org.
- **NPPES:** the bulk files are at https://download.cms.gov/nppes/NPI_Files.html. The API caps at 1,200 results per query.
