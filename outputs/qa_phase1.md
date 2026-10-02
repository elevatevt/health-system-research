# Phase 1 QA

Systems: **480** (nonprofit 439, church-operated 40, missing code 1). Member hospitals: 2977 (2697 acute).

- [PASS] every system has >=1 acute hospital: min 1
- [PASS] member acute count equals AHRQ acutehosp_cnt
- [PASS] member count equals AHRQ hosp_cnt
- [PASS] footprint (system,state) pairs reconcile to hospital file: 679 vs 679
- [PASS] system_id unique

Mixed ownership (>=1 acute hospital coded public/for-profit/other): **73** systems.
HQ state not in hospital footprint: CommonSpirit Health (IL), Covenant Health Systems (MA), Ascension Health (MO).
Multi-state systems: 85.

## Systems by HQ state

| State | Systems |
|---|---|
| AK | 2 |
| AL | 2 |
| AR | 9 |
| AZ | 7 |
| CA | 33 |
| CO | 7 |
| CT | 8 |
| DC | 1 |
| DE | 3 |
| FL | 18 |
| GA | 12 |
| HI | 3 |
| IA | 4 |
| ID | 3 |
| IL | 20 |
| IN | 13 |
| KS | 3 |
| KY | 12 |
| LA | 6 |
| MA | 18 |
| MD | 13 |
| ME | 6 |
| MI | 10 |
| MN | 14 |
| MO | 18 |
| MS | 2 |
| MT | 6 |
| NC | 9 |
| ND | 2 |
| NE | 9 |
| NH | 6 |
| NJ | 17 |
| NM | 3 |
| NV | 2 |
| NY | 39 |
| OH | 28 |
| OK | 3 |
| OR | 7 |
| PA | 30 |
| RI | 3 |
| SC | 5 |
| SD | 3 |
| TN | 8 |
| TX | 15 |
| UT | 1 |
| VA | 11 |
| VT | 2 |
| WA | 9 |
| WI | 11 |
| WV | 4 |
