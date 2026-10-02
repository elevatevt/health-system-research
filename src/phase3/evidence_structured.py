"""Phase 3 structured evidence for a set of systems: URAC roster and NPPES specialty-pharmacy NPIs.

Produces *candidates*, not tier calls. A candidate links a URAC record or NPI to a system by:
  - name: a distinctive token set from the system name or a member hospital name is contained in the
    organization's legal/DBA name, within the system's footprint states; or
  - address: same normalized street line and ZIP5 as a member hospital.
Common single-word names (Mercy, Baptist...) will over-match; reviewers confirm or reject each candidate.

Outputs (for systems listed in --systems CSV, default the pilot list):
  outputs/phase3_<tag>_urac_candidates.csv
  outputs/phase3_<tag>_nppes_candidates.csv
Raw NPPES responses are cached in data/raw/nppes/ (gitignored).
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import OUT, RAW, load_hospitals  # noqa: E402

ACHC_DIR = RAW / "achc"
# ACHC organization directory (organization.achc.org), pulled with the page's own filter request:
# program 6 Pharmacy + service 18 Specialty Pharmacy Services / 22 Infusion Pharmacy Services; program 22 Home Infusion Therapy.
ACHC_LISTS = {"pharmacy_specialty": "Pharmacy: Specialty Pharmacy Services",
              "pharmacy_infusion": "Pharmacy: Infusion Pharmacy Services",
              "home_infusion": "Home Infusion Therapy"}
ACHC_AS_OF = "2026-10-02"
URAC_FILE = RAW / "urac_accreditation_rosters_2026-09-23.xlsx"
URAC_AS_OF = "2026-09-23"
URAC_SHEETS = ["Specialty Pharmacy", "Specialty Pharmacy Services", "Infusion Pharmacy", "Rare Disease Pharm COE"]
SPECIALTY_TAXONOMY = "3336S0011X"
NPPES_API = "https://npiregistry.cms.hhs.gov/api/"
NPPES_CACHE = RAW / "nppes"

STOP = set("""health system systems services service inc llc lp llp the of and a an on behalf its it's for
hospital hospitals medical center centers centre corporation corp healthcare care clinic clinics university
pharmacy pharmacies specialty dba d b a network group regional community memorial saint st general foundation
infusion home outpatient retail rx company co association partners enterprises holdings""".split())


def tokens(name) -> frozenset:
    s = re.sub(r"['\u2019`]", "", str(name).lower())  # Children's -> childrens
    return frozenset(t for t in re.findall(r"[a-z0-9]+", s) if t not in STOP and len(t) > 2)


def norm_street(s) -> str:
    s = str(s).lower()
    s = re.sub(r"\b(suite|ste|unit|bldg|building|floor|fl|room|rm)\b.*", "", s)
    for a, b in [("street", "st"), ("avenue", "ave"), ("road", "rd"), ("drive", "dr"), ("boulevard", "blvd"),
                 ("lane", "ln"), ("parkway", "pkwy"), ("highway", "hwy"), ("north", "n"), ("south", "s"),
                 ("east", "e"), ("west", "w")]:
        s = re.sub(rf"\b{a}\b", b, s)
    return re.sub(r"[^a-z0-9]", "", s)


def system_keys(sys_row, members: pd.DataFrame) -> list[tuple[frozenset, str]]:
    """Distinctive token sets to look for in pharmacy names, with what each came from."""
    sys_tok = tokens(sys_row.system_name)
    keys = [(sys_tok, f"system name: {sys_row.system_name}")] if sys_tok else []
    for name in members.hospital_name.dropna().unique():
        t = tokens(name)
        if len(t) >= 2 or (t and t <= sys_tok):
            keys.append((t, f"member hospital: {name}"))
    return keys


def load_urac() -> pd.DataFrame:
    frames = [pd.read_excel(URAC_FILE, sheet_name=s, header=3).dropna(subset=["Cert #"]) for s in URAC_SHEETS]
    u = pd.concat(frames, ignore_index=True).rename(columns={
        "Cert #": "urac_cert", "Program": "program", "Status": "status", "Organization": "organization",
        "Street Address": "street", "City": "city", "State": "state", "ZIP": "zip",
        "Effective Date": "effective_date", "Expiration Date": "expiration_date", "Directory Detail URL": "evidence_url"})
    u["tok"] = u.organization.map(tokens)
    u["street_n"] = u.street.map(norm_street)
    u["zip5"] = u.zip.astype(str).str[:5]
    return u[["urac_cert", "program", "status", "organization", "street", "city", "state", "zip5",
              "effective_date", "expiration_date", "evidence_url", "tok", "street_n"]]


def load_achc() -> pd.DataFrame:
    import html as htmlmod
    rows = []
    for tag, label in ACHC_LISTS.items():
        r = json.loads((ACHC_DIR / f"{tag}_20261002.json").read_text(encoding="utf-8"))
        for li in re.findall(r"<li>(.*?)</li>", r["response_html"], flags=re.S):
            def grab(pat):
                m = re.search(pat, li, flags=re.S)
                return htmlmod.unescape(m.group(1).strip()) if m else ""
            ps = re.findall(r"<p>([^<]*)</p>", li)
            cityline = htmlmod.unescape(ps[1].strip()) if len(ps) > 1 else ""
            m = re.match(r"(.*),\s*([A-Z]{2})\s+(\d{5})", cityline)
            cid = grab(r'data-company-id="(\d+)"')
            rows.append({"achc_list": label, "achc_company_id": cid,
                         "organization": grab(r'class="company_name">(.*?)</b>'),
                         "dba": grab(r'class="dba_company">(.*?)</b>'),
                         "street": htmlmod.unescape(ps[0].strip().rstrip(",")) if ps else "",
                         "city": m.group(1) if m else cityline, "state": m.group(2) if m else "",
                         "zip5": m.group(3) if m else "",
                         "evidence_url": htmlmod.unescape(grab(r'href="(https://organization\.achc\.org/print\?[^"]*)"')).replace(" ", "%20")})
    a = pd.DataFrame(rows)
    a["tok"] = [tokens(o) | tokens(d) for o, d in zip(a.organization, a.dba)]
    a["street_n"] = a.street.map(norm_street)
    return a


def nppes_state(state: str) -> list[dict]:
    """All NPI-2 records in a state with the Specialty Pharmacy taxonomy in any position (cached)."""
    NPPES_CACHE.mkdir(parents=True, exist_ok=True)
    path = NPPES_CACHE / f"specialty_{state}_{date.today():%Y%m%d}.json"
    if path.exists():
        return json.loads(path.read_text())
    results = []
    for skip in range(0, 1200, 200):
        params = {"version": "2.1", "taxonomy_description": "Specialty Pharmacy", "state": state,
                  "enumeration_type": "NPI-2", "limit": 200, "skip": skip}
        with urllib.request.urlopen(NPPES_API + "?" + urllib.parse.urlencode(params), timeout=60) as r:
            page = json.load(r).get("results", [])
        results += page
        time.sleep(0.3)
        if len(page) < 200:
            break
    if len(results) >= 1200:
        print(f"WARNING: {state} hit the NPPES API 1,200-result cap; use the bulk file", file=sys.stderr)
    path.write_text(json.dumps(results))
    return results


def nppes_frame(states) -> pd.DataFrame:
    rows = []
    for st in sorted(states):
        for r in nppes_state(st):
            codes = [t["code"] for t in r.get("taxonomies", [])]
            if SPECIALTY_TAXONOMY not in codes:
                continue
            b = r["basic"]
            names = [b.get("organization_name", "")] + [o.get("organization_name", "") for o in r.get("other_names", [])]
            loc = next((a for a in r.get("addresses", []) if a.get("address_purpose") == "LOCATION"), {})
            primary = next((t for t in r["taxonomies"] if t.get("primary")), {})
            rows.append({
                "npi": r["number"], "org_name": b.get("organization_name"),
                "other_names": "; ".join(sorted({n for n in names[1:] if n and n != names[0]})),
                "specialty_is_primary": primary.get("code") == SPECIALTY_TAXONOMY,
                "primary_taxonomy": primary.get("desc"),
                "street": loc.get("address_1"), "city": loc.get("city"), "state": loc.get("state"),
                "zip5": str(loc.get("postal_code", ""))[:5],
                "authorized_official_title": b.get("authorized_official_title_or_position"),
                "status": b.get("status"), "last_updated": b.get("last_updated"),
                "tok": frozenset().union(*(tokens(n) for n in names)),
                "street_n": norm_street(loc.get("address_1", "")),
            })
    return pd.DataFrame(rows).drop_duplicates("npi")  # API paging can repeat records


def match(systems: pd.DataFrame, hospitals: pd.DataFrame, cand: pd.DataFrame, state_col: str) -> list[dict]:
    out = []
    for s in systems.itertuples():
        members = hospitals[hospitals.health_sys_id == s.system_id]
        states = set(s.footprint_states.split(";")) | {s.hq_state}
        pool = cand[cand[state_col].isin(states)]
        addr = {(norm_street(h.hospital_street), str(h.hospital_zip)[:5]): h.hospital_name for h in members.itertuples()}
        keys = system_keys(s, members)
        for c in pool.itertuples(index=False):
            basis = [why for k, why in keys if k <= c.tok]
            hit = addr.get((c.street_n, c.zip5))
            if hit:
                basis.append(f"address = member hospital: {hit}")
            if basis:
                out.append({"system_id": s.system_id, "system_name": s.system_name, "match_basis": " | ".join(basis[:3]),
                            **{k: v for k, v in c._asdict().items() if k not in ("tok", "street_n")}})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default=str(OUT / "phase3_pilot_systems.csv"))
    ap.add_argument("--tag", default="pilot")
    args = ap.parse_args()

    systems = pd.read_csv(args.systems)
    hospitals = load_hospitals()

    urac = load_urac()
    u = pd.DataFrame(match(systems, hospitals, urac, "state"))
    u["evidence_as_of"] = URAC_AS_OF
    u.to_csv(OUT / f"phase3_{args.tag}_urac_candidates.csv", index=False)

    achc = load_achc()
    a = pd.DataFrame(match(systems, hospitals, achc, "state"))
    a["evidence_as_of"] = ACHC_AS_OF
    a.to_csv(OUT / f"phase3_{args.tag}_achc_candidates.csv", index=False)

    states = set(";".join(systems.footprint_states).split(";")) | set(systems.hq_state)
    npi = nppes_frame(states)
    n = pd.DataFrame(match(systems, hospitals, npi, "state"))
    n["evidence_url"] = "https://npiregistry.cms.hhs.gov/provider-view/" + n.npi
    n["evidence_as_of"] = date.today().isoformat()
    n.to_csv(OUT / f"phase3_{args.tag}_nppes_candidates.csv", index=False)

    print(f"URAC pharmacy records: {len(urac)}; NPPES specialty NPIs in {len(states)} states: {len(npi)}")
    print(f"URAC candidates: {len(u)} for {u.system_id.nunique()} of {len(systems)} systems")
    print(f"ACHC records: {len(achc)}; candidates: {len(a)} for {a.system_id.nunique()} of {len(systems)} systems")
    print(f"NPPES candidates: {len(n)} for {n.system_id.nunique()} of {len(systems)} systems")
    summary = systems[["system_id", "system_name"]].assign(
        urac=systems.system_id.map(u.groupby("system_id").size()).fillna(0).astype(int),
        achc=systems.system_id.map(a.groupby("system_id").size()).fillna(0).astype(int),
        nppes=systems.system_id.map(n.groupby("system_id").size()).fillna(0).astype(int))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
