# Phase 3 decisions

| Date (ET) | Decision | By |
|---|---|---|
| 2026-10-02 | Full run classifies systems as they exist today, to the extent possible. | Nate |
| 2026-10-02 | Status rules approved: renamed → classify under new name; acquired/merged → acquirer's pharmacy if it serves these hospitals ("via X"), flag duplicates; partly closed → operating hospitals; closed → no tier, excluded from counts. List stays the 480 AHRQ systems; revenue/hospital data stay 2023. | Nate |
| 2026-10-02 | Appearing on the Shields Health Solutions partner list is enough for "Managed or partnered" (applied in consolidate.py from the list retrieved 2026-10-02). | Nate |
| 2026-10-02 | URAC/ACHC accreditation counts as current until a lapse is confirmed, even past the roster expiration date. | Nate |
| 2026-10-02 | Full run chunked: ~1M tokens now (groups 001–009 + pilot refresh), remainder scheduled 2026-10-02 14:30 EDT. | Nate |

## Default applied, awaiting confirmation
- Parent/JV: a pharmacy held by a parent that controls the system counts as system-owned (Mayo Foundation). A co-owned JV counts only when the system has no wholly owned specialty pharmacy, and is "Managed or partnered" if an outside manager runs it (UPMC/Chartwell not counted).
