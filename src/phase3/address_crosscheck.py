"""Find URAC/ACHC records at the address of any NPI a reviewer cited but whose record the row doesn't list.

Catches accreditations held under a subsidiary's legal name at a non-hospital pharmacy site
(e.g. Infirmary Health -> Gulf Health Hospitals "NBI Specialty Pharmacy", URAC SPP010729).
Output: outputs/phase3_address_crosscheck.csv. Confirmed hits go into manual_corrections.json by hand
(shared buildings produce false positives, e.g. other tenants' pharmacies).
"""
import glob
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, RAW  # noqa: E402
from evidence_structured import load_achc, load_urac, norm_street  # noqa: E402


def main() -> None:
    u, a = load_urac(), load_achc()
    npi_addr = {}
    for f in glob.glob(str(RAW / "nppes" / "specialty_*.json")):
        for r in json.loads(Path(f).read_text(encoding="utf-8")):
            loc = next((x for x in r.get("addresses", []) if x.get("address_purpose") == "LOCATION"), {})
            npi_addr[r["number"]] = (norm_street(loc.get("address_1", "")), str(loc.get("postal_code", ""))[:5])
    f = pd.concat([pd.read_csv(OUT / f"phase3_{t}_classification.csv") for t in ("pilot", "full")])
    rows = []
    for r in f.itertuples():
        have = str(r.accreditations)
        for n in set(re.findall(r"\b1\d{9}\b", " ".join(map(str, (r.evidence_urls, r.confirmed_candidates, r.tier_source))))):
            if n not in npi_addr:
                continue
            st, z = npi_addr[n]
            for x in u[(u.street_n == st) & (u.zip5 == z)].itertuples():
                if x.urac_cert not in have:
                    rows.append((r.system_id, r.system_name, r.tier, r.confidence, n, f"URAC {x.urac_cert}", x.program, x.organization))
            for x in a[(a.street_n == st) & (a.zip5 == z)].itertuples():
                if str(x.achc_company_id) not in have:
                    rows.append((r.system_id, r.system_name, r.tier, r.confidence, n, f"ACHC {x.achc_company_id}", x.achc_list, f"{x.organization} / {x.dba}"))
    d = pd.DataFrame(rows, columns=["system_id", "system_name", "tier", "confidence", "npi", "record", "program", "organization"])
    d = d.drop_duplicates(["system_id", "record"])
    d.to_csv(OUT / "phase3_address_crosscheck.csv", index=False)
    print(f"{len(d)} unlisted records across {d.system_id.nunique()} systems")


if __name__ == "__main__":
    main()
