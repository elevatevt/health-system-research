# Phase 3 full run: runbook

**Status 2026-10-02: complete.** All 91 groups, the status pass and the Unknown recheck are done. Use this runbook only to re-run or refresh.

Repo: `C:\dev\health-system-research`. Python: `.venv\Scripts\python.exe`. Public data only.

## State
- `outputs/phase3_full_systems.csv`: the 455 systems not in the pilot, largest first.
- `data/raw/phase3_full/group_001.json` … `group_091.json`: reviewer packets of 5 systems each, gitignored.
- `docs/phase3_reviewer_prompt.md`: reviewer instructions with Nate's 2026-10-02 decisions. It is the single source for the rules.
- A group is done when `data/raw/phase3_full/group_NNN_result.json` exists and parses as JSON.
- Chunk 1 (2026-10-02 morning) covered groups 001–009 plus the pilot refresh. Chunk 2 (scheduled 2026-10-02 14:30 EDT) covers every group without a valid result.

## Run a chunk
1. List groups without a valid result file:
   ```
   .venv\Scripts\python.exe -c "import json,glob,os; d='data/raw/phase3_full'; print([f'{i:03d}' for i in range(1,92) if not (os.path.exists(f'{d}/group_{i:03d}_result.json') and json.load(open(f'{d}/group_{i:03d}_result.json',encoding='utf-8')) is not None)])"
   ```
   A file that fails to parse counts as missing.
2. For each missing group, start a background `general-purpose` Agent on model `sonnet` with exactly this prompt (NNN = group number):
   ```
   Read C:\dev\health-system-research\docs\phase3_reviewer_prompt.md and follow it exactly, substituting:
   {packet} = C:\dev\health-system-research\data\raw\phase3_full\group_NNN.json
   {result} = C:\dev\health-system-research\data\raw\phase3_full\group_NNN_result.json
   {today} = <today's date, YYYY-MM-DD>
   ```
   Run about 10 agents at a time and start the next wave as agents finish. Each agent uses about 100K tokens.
3. When all groups have results, rerun step 1 and retry any group that is still missing or invalid, once.
3a. **Status pass.** Some results lack a verified status (no recorded search). Run:
   ```
   .venv\Scripts\python.exe src\phase3\consolidate.py --tag full
   .venv\Scripts\python.exe src\phase3\status_batches.py
   ```
   It writes `data\raw\phase3_full\statusbatch_NN.json` (10 systems each) and prints an agent prompt template.
   For each batch NN, start a background `general-purpose` Agent on `sonnet` with that template, filling {today},
   {batch} = the statusbatch_NN.json path and {result} = `C:\dev\health-system-research\data\raw\phase3_full\status_pass_NN.json`.
   Run about 10 at a time. Skip a batch whose status_pass_NN.json already exists and parses.
   If the pass finds a system "acquired by" or "merged into" another, note it in the report; build_final.py flags
   systems absorbed into another listed system, and Nate decides whether the tier should follow the acquirer.
4. Merge and check:
   ```
   .venv\Scripts\python.exe src\phase3\consolidate.py --tag full
   .venv\Scripts\python.exe src\phase3\consolidate.py --tag pilot
   .venv\Scripts\python.exe src\build_final.py
   ```
   `build_final.py` writes the deliverable `outputs/final_nonprofit_systems.csv` and lists the excluded for-profit conversions in `outputs/excluded_now_for_profit.csv`.
5. Commit `outputs/phase3_full_*`, `outputs/phase3_pilot_*`, `outputs/final_nonprofit_systems.csv` and `outputs/excluded_now_for_profit.csv` with a plain `git commit`, using the global git identity; never override user.email. Do **not** push; Nate pushes.
6. Report the tier counts, the systems with status ≠ unchanged, the rule adjustments, and any groups that failed.

## Do not
- Change the reviewer prompt or the tier rules.
- Fetch the URAC directory (its terms bar automated access; the roster file in data/raw is used instead).
- Touch any repo other than this one, or any client data.
