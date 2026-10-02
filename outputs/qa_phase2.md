# Phase 2 QA

Systems: 480.
- Compendium revenue missing: **5** (Nicklaus Childrens Health System, Shriners Hospitals for Children, University of Miami Health System, Interfaith Medical Center, East Tennessee Childrens Hospital Association).
- FY2024 rebuild missing (no member cost reports): 12.
- Systems with >=1 acute member lacking a cost report: Compendium 127, FY2024 140, either 149.
- Acute member hospitals: 2697; FY2024 cost report found 2399 (89.0%); annualized 60; covering <300 days 30.
- Totals where both exist (466 systems): Compendium $918.6B, FY2024 $1,005.1B.
- Median FY2024 vs Compendium gap: all 10.4%; same hospital coverage (423 systems) 10.5%.
- Member hospitals flagged as likely cost-report errors (negative NPR or FY2024/Compendium ratio outside 0.5-2.0x): 19 in 14 systems (7 negative). Source values are kept as published.
- **Gap >25%: 49 systems** (15 of them have different hospital coverage between the two years).

## Hospital-level outliers

| Hospital | State | System | Compendium $M | FY2024 $M |
|---|---|---|---|---|
| Alle-Kiski Medical Center | PA | HSI00000025 | 109 | -19 |
| Aspirus Rhinelander Hospital | WI | HSI00000057 | -363 | 245 |
| Aspirus Riverview Hospital & Clinics | WI | HSI00000057 | 161 | 62 |
| Divine Savior Hospital | WI | HSI00000057 | 20 | 70 |
| Banner Ocotillo Medical Center | AZ | HSI00000073 | 419 | 111 |
| St. Josephs Comm. Hospt. | WI | HSI00000386 | 437 | 150 |
| North Baldwin Infirmary | AL | HSI00000511 | 55 | 121 |
| Kaiser Sunnyside Medical Center | OR | HSI00000536 | nan | -0 |
| Kaiser Westside Medical Center | OR | HSI00000536 | nan | -0 |
| Mercy Health/Love County | OK | HSI00000660 | 11 | 5 |
| Mercy Health System Corporation | WI | HSI00000667 | -130 | -199 |
| Montefiore New Rochelle Hospital | NY | HSI00000700 | 163 | 612 |
| The Mount Vernon Hospital | NY | HSI00000700 | 58 | 266 |
| Mount Sinai Health System-Beth Israe | NY | HSI00000711 | 2,946 | 737 |
| Huntington Hospital | NY | HSI00000767 | 647 | 1,997 |
| Community Health Center Branch | MI | HSI00000848 | 76 | 272 |
| St. Lukes Hospital | PA | HSI00000936 | 8,944 | 1,439 |
| Lake View Memorial Hospital | MN | HSI00000937 | 23 | -7 |
| St. Lukes Hospital Of Duluth | MN | HSI00000937 | 507 | -589 |

## Systems with >25% gap

| System | HQ | Compendium $M | FY2024 $M | Gap % | Missing CR (Comp/FY24) | Hospital outlier |
|---|---|---|---|---|---|---|
| Saint Lukes Hospital of Duluth | MN | 530 | -595 | -212.4 | 0/0 | yes |
| Baptist Healthcare System | KY | 3,554 | 849 | -76.1 | 0/6 |  |
| Mercyhealth | WI | 881 | 220 | -75.0 | 0/1 | yes |
| Saint Lukes University Health Network | PA | 10,270 | 3,142 | -69.4 | 2/2 | yes |
| Northwestern Medicine | IL | 6,057 | 2,815 | -53.5 | 1/8 |  |
| Emory Healthcare | GA | 4,262 | 2,155 | -49.4 | 0/5 |  |
| Community Hospital Corporation | TX | 904 | 567 | -37.3 | 1/2 |  |
| Mass General Brigham | MA | 9,439 | 6,826 | -27.7 | 0/2 |  |
| UMass Memorial Health Care | MA | 2,635 | 3,300 | +25.2 | 2/2 |  |
| Lecom Health | PA | 86 | 109 | +26.1 | 0/0 |  |
| University of Rochester Medical Center | NY | 4,164 | 5,254 | +26.2 | 0/0 |  |
| Duke University Health System | NC | 4,261 | 5,383 | +26.3 | 0/1 |  |
| University Health | MO | 700 | 884 | +26.3 | 0/0 |  |
| Dartmouth-Hitchcock | NH | 2,218 | 2,806 | +26.5 | 0/0 |  |
| Avera Health | SD | 2,517 | 3,186 | +26.5 | 4/3 |  |
| Mercy Medical Center | IA | 401 | 508 | +26.6 | 0/0 |  |
| Bassett Healthcare Network | NY | 711 | 901 | +26.7 | 0/0 |  |
| Enloe Medical Center | CA | 834 | 1,058 | +26.8 | 0/0 |  |
| Vanderbilt Health | TN | 5,729 | 7,265 | +26.8 | 0/0 |  |
| The Nebraska Medical Center | NE | 1,589 | 2,022 | +27.2 | 0/0 |  |
| Jefferson Hospital Association | AR | 202 | 258 | +28.1 | 0/0 |  |
| Caromont Health System | NC | 642 | 823 | +28.2 | 0/0 |  |
| Piedmont Healthcare | GA | 5,662 | 7,292 | +28.8 | 1/1 |  |
| Temple University Health System | PA | 2,123 | 2,749 | +29.5 | 1/1 |  |
| Lehigh Valley Health Network | PA | 3,400 | 4,406 | +29.6 | 5/4 |  |
| Multicare Health System | WA | 3,559 | 4,618 | +29.8 | 1/0 |  |
| Gerald Champion Regional Medical Center | NM | 246 | 323 | +31.5 | 0/0 |  |
| Bayhealth | DE | 887 | 1,171 | +32.0 | 0/0 |  |
| Wayne Memorial Health System | PA | 104 | 137 | +32.4 | 0/0 |  |
| Meritus Health | MD | 396 | 525 | +32.4 | 0/0 |  |
| Geisinger | PA | 3,221 | 4,269 | +32.5 | 2/2 |  |
| Cayuga Medical Center | NY | 303 | 403 | +32.8 | 1/0 |  |
| Saint Charles Health System | OR | 864 | 1,157 | +33.9 | 1/1 |  |
| Davis Health System | WV | 137 | 184 | +34.0 | 0/0 |  |
| Childrens Hospital of the Kings Daughters Health System | VA | 546 | 733 | +34.3 | 0/0 |  |
| Great River Health Systems | IA | 302 | 410 | +35.6 | 0/0 |  |
| Southeast Alaska Regional Health Consortium | AK | 34 | 46 | +35.7 | 2/2 |  |
| Stamford Health | CT | 834 | 1,140 | +36.6 | 0/0 |  |
| Renown Health | NV | 1,099 | 1,510 | +37.4 | 1/0 |  |
| UC Health | OH | 1,617 | 2,249 | +39.1 | 0/0 |  |
| Childrens Hospital and Medical Center | NE | 501 | 710 | +41.6 | 0/0 |  |
| Sarah Bush Lincoln Health System | IL | 449 | 638 | +42.2 | 0/0 |  |
| Memorial Healthcare | MI | 226 | 325 | +43.6 | 0/0 |  |
| OU Health | OK | 1,647 | 2,411 | +46.4 | 1/1 |  |
| Mohawk Valley Health System | NY | 413 | 620 | +50.1 | 0/0 |  |
| Aspirus | WI | 1,117 | 1,836 | +64.4 | 1/1 | yes |
| Parkview Health System | IN | 549 | 2,348 | +327.3 | 1/0 |  |
| CAMC Health System | WV | 531 | 2,482 | +367.4 | 3/1 |  |
| Gundersen Health System | WI | 174 | 835 | +381.0 | 2/1 |  |
