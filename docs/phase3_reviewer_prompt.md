You are classifying US non-profit health systems by specialty pharmacy capability. Public data only. Read-only web research: do not log in, submit forms, accept terms, or download files; decline non-essential cookies. Today is {today}.

INPUT: read {packet}. It holds up to 5 systems, each with its member hospitals (AHRQ Compendium 2023) and CANDIDATE evidence that was name- or address-matched automatically:
- urac: URAC accreditation roster records (Specialty Pharmacy, Specialty Pharmacy Services, Infusion Pharmacy, Rare Disease COE), as of 2026-09-23.
- achc: ACHC directory records (Pharmacy program with Specialty Pharmacy Services or Infusion Pharmacy Services, or the Home Infusion Therapy program), as of 2026-10-02.
- nppes: NPI-2 records carrying taxonomy 3336S0011X "Specialty Pharmacy" in any position, as of 2026-10-02.
The matcher over-matches. Many candidates are false positives: a different system sharing a word like Methodist, Mercy, Baptist or Children's, or an unrelated retail chain. Confirm or reject EVERY candidate, giving a reason. Candidates can also miss a pharmacy, so do your own search.
Also read C:\dev\health-system-research\data\raw\shields_partners_20261002.txt, the Shields Health Solutions partner list as of 2026-10-02.

CLASSIFY EACH SYSTEM AS IT EXISTS TODAY.
First establish the system's current status, using the system's website and news:
- status_since_2023 is one of "unchanged", "renamed", "acquired by", "merged into", "partly closed" or "closed".
- Renamed: classify under the new name.
- Acquired by or merged into another system: the tier reflects the acquirer's specialty pharmacy if it serves these hospitals. Say "via <acquirer>" in tier_source and give current_parent.
- Partly closed: classify the hospitals still operating.
- Closed entirely: set tier to "" (blank) and confidence to "". Give the closure evidence.
- Now for-profit (acquired by or converted to a for-profit owner such as HCA, Tenet, CHS, LifePoint, UHS, Ardent, Prime or ScionHealth): set now_for_profit to true, tier "" and confidence "", give the evidence, and skip the pharmacy research. These systems are excluded from the deliverable (decision 2026-10-02). Otherwise now_for_profit is false.

FOR EACH SYSTEM:
1. Search the system's own website and press releases for "specialty pharmacy", "home infusion", "infusion pharmacy" and "outpatient pharmacy". Use WebSearch and WebFetch, and record each site/page you checked in sources_searched.
2. Check whether the pharmacy is run or managed by an outside party: Shields Health Solutions, Trellis Rx (CPS), Comprehensive Pharmacy Services, CarepathRx, Walgreens or CVS joint ventures, Optum, or any "in partnership with". **Rule: if the system appears on the Shields partner list, that alone is enough for "Managed or partnered" with manager_partner "Shields Health Solutions".**
3. Check whether the owning legal entity of each confirmed URAC/ACHC record is the system, a member hospital, or a system subsidiary.
   - A pharmacy held by a parent organization that controls the system counts as system-owned (example: Mayo Foundation for Mayo Clinic Health System).
   - A joint venture the system co-owns with others counts only if the system has no wholly owned specialty pharmacy. If it is run by an outside manager, it is "Managed or partnered". Always mention a JV in notes.

ACCREDITATION RULE: treat a URAC or ACHC record as current even if its listed expiration date has passed, unless you find evidence that it lapsed.

TIERS (pick exactly one per system that is not closed):
- "Owned, accredited": system-owned specialty pharmacy holding URAC Specialty Pharmacy or ACHC Specialty Pharmacy Services accreditation (or NABP/NCQA specialty).
- "Owned, not accredited": system-owned pharmacy dispensing specialty drugs, with no specialty accreditation found.
- "Managed or partnered": specialty pharmacy run under a named outside manager or partner, or the system is on the Shields partner list. This takes precedence over the Owned tiers. Still record any accreditation.
- "Infusion or home infusion only": infusion or home-infusion pharmacy only; no retail specialty dispensing found.
- "None found": you searched the system's own website/press releases AND the candidates were all rejected or absent. List the website pages in sources_searched.
- "Unknown": evidence conflicts or is too thin, or you could not search the system's own website.
Unknown is not "None found". Never infer absence from silence without having searched.

CONFIDENCE: High = a confirmed accreditation record (or explicit system web page) plus a second agreeing source. Medium = one strong source. Low = NPPES-only or ambiguous evidence. A single NPPES hit with no corroboration is capped at Low.

MINIMUM WORK PER SYSTEM (do not go below this):
- One status search, e.g. "<system name> merger OR acquisition OR renamed OR closed 2024 2025 2026". Put the URL that shows the current status in status_evidence_url, even when the status is "unchanged" (a current system page or news item showing the same name and structure is fine). Never write "unchanged" without that URL. Record the exact status search you ran in status_search_query.
- One specialty-pharmacy search.
- Fetch at least one page on the system's own website whenever no URAC/ACHC candidate is confirmed, or the tier would be "None found", "Unknown" or "Owned, not accredited".
Stay around 3-6 searches/fetches per system. Do not fetch the URAC or ACHC directories; the candidates already carry their evidence URLs.

OUTPUT: write a JSON array (one object per system in the packet) to {result}, with these keys:
system_id, system_name, current_name, status_since_2023, current_parent, status_evidence_url, status_change_date, status_search_query, now_for_profit (true/false), tier, confidence, tier_source (short: which source(s) drove the call), pharmacy_names (list), owning_entity, accreditations (list like "URAC SPP010062 Specialty Pharmacy", "ACHC 88449 Specialty Pharmacy Services"), manager_partner (name or ""), evidence_urls (list), evidence_date (publication or last-updated date of the key web source if shown, otherwise {today}), confirmed_candidates (list of ids), rejected_candidates (list of "id: reason"), sources_searched (list), notes (max 2 sentences).
Validate the file by running:
  C:\dev\health-system-research\.venv\Scripts\python.exe -c "import json; print(len(json.load(open(r'{result}', encoding='utf-8'))))"
Fix it if that fails. Then reply with only: "<packet name>: <n> systems written" plus at most 3 lines of reviewer flags.
