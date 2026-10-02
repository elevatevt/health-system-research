"""Resolve an absorbed system's current_parent to another listed system (strict matching).

A listed system is the acquirer when its name tokens equal the parent's tokens, or one contains the
other with at least two distinctive tokens, AND the two systems share a footprint state.
"""
import pandas as pd

from evidence_structured import tokens


def resolve(df: pd.DataFrame, footprints: dict) -> dict:
    names = {r.system_id: (tokens(r.system_name), tokens(r.current_name) if isinstance(r.current_name, str) else frozenset())
             for r in df.itertuples()}
    out = {}
    for r in df[df.status_since_2023.isin(["acquired by", "merged into"])].itertuples():
        pt = tokens(r.current_parent) if isinstance(r.current_parent, str) else frozenset()
        if not pt:
            continue
        hits = []
        for sid, (nt, ct) in names.items():
            if sid == r.system_id:
                continue
            for t in (nt, ct):
                close = t and (t == pt or ((t <= pt or pt <= t) and min(len(t), len(pt)) >= 2))
                if close and footprints.get(sid, set()) & footprints.get(r.system_id, set()):
                    hits.append(sid)
                    break
        if hits:
            out[r.system_id] = hits
    return out
