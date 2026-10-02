# Phase 3 decisions

| Date (ET) | Decision | By |
|---|---|---|
| 2026-10-02 | Full run classifies systems as they exist today, to the extent possible. | Nate |
| 2026-10-02 | Status rules approved: renamed → classify under new name; acquired/merged → acquirer's pharmacy if it serves these hospitals ("via X"), flag duplicates; partly closed → operating hospitals; closed → no tier, excluded from counts. List stays the 480 AHRQ systems; revenue/hospital data stay 2023. | Nate |
| 2026-10-02 | Appearing on the Shields Health Solutions partner list is enough for "Managed or partnered" (applied in consolidate.py from the list retrieved 2026-10-02). | Nate |
| 2026-10-02 | URAC/ACHC accreditation counts as current until a lapse is confirmed, even past the roster expiration date. | Nate |
| 2026-10-02 | Systems acquired by or converted to a for-profit owner since 2023 are excluded from the deliverable (listed in outputs/excluded_now_for_profit.csv). First case: Catholic Medical Center (HCA, 2025-02). | Nate |
| 2026-10-02 | Full run chunked: ~1M tokens now (groups 001–009 + pilot refresh), remainder scheduled 2026-10-02 14:30 EDT. | Nate |

## Run log
- 2026-10-02: full run completed in this session (91 reviewer groups, 6 status-pass batches, 6 blocked-site recheck batches). The 14:30 scheduled fallback was disabled because nothing remained. Results: `outputs/phase3_summary.md`.
- Excluded as now for-profit: Catholic Medical Center (HCA, 2025-02), Summa Health (HATCo/General Catalyst, 2025-10). Central Maine Healthcare was acquired by Prime Healthcare Foundation, a nonprofit, so it stays in.
- Rule fixes made during the run: whole-word for-profit parent matching (BJC Healthcare had matched "hca"); the parent backstop applies only when the reviewer did not answer now_for_profit; status needs a recorded search query; acquirer matching requires close names plus a shared footprint state.

## Default applied, awaiting confirmation
- Parent/JV: a pharmacy held by a parent that controls the system counts as system-owned (Mayo Foundation). A co-owned JV counts only when the system has no wholly owned specialty pharmacy, and is "Managed or partnered" if an outside manager runs it (UPMC/Chartwell not counted).
