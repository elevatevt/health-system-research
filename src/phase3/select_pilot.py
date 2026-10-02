"""Pick the 25-system Phase 3 pilot: 5 per acute-bed quintile, distinct HQ states where possible."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import OUT  # noqa: E402

SEED = 20261002
PER_BAND = 5


def main() -> None:
    s = pd.read_csv(OUT / "nonprofit_systems_combined.csv")
    s["size_band"] = pd.qcut(s.total_beds.rank(method="first", na_option="bottom"), 5, labels=["Q1 smallest", "Q2", "Q3", "Q4", "Q5 largest"])
    picks, used_states = [], set()
    for band, g in s.groupby("size_band", observed=True):
        g = g.sample(frac=1, random_state=SEED)
        fresh = g[~g.hq_state.isin(used_states)]
        chosen = pd.concat([fresh, g.drop(fresh.index)]).head(PER_BAND)
        used_states |= set(chosen.hq_state)
        picks.append(chosen)
    pilot = pd.concat(picks)[["system_id", "system_name", "hq_city", "hq_state", "footprint_states", "size_band",
                              "n_hospitals", "n_acute_hospitals", "total_beds", "npr_compendium", "ownership_label"]]
    pilot.to_csv(OUT / "phase3_pilot_systems.csv", index=False)
    print(pilot.to_string(index=False))
    print("distinct HQ states:", pilot.hq_state.nunique())


if __name__ == "__main__":
    main()
