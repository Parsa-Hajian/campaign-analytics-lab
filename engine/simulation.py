"""Event simulation engine: campaign shapes, shock multipliers, attribution."""
import numpy as np
import pandas as pd
from datetime import timedelta

from config import EVENT_MAPPING


def get_shock_multiplier(dt, shocks):
    """Return the total shock multiplier for a given date across all active shocks.

    Campaign shape functions (p = days_elapsed / duration):
        Email Campaign  (Front-Loaded): lift × e^(-3p)
        Flash Sale      (Linear Fade):  lift × (1 - p)
        Product Launch  (Delayed Peak): lift × Gaussian(p; μ=0.4, σ=0.3)
        Awareness Drive (Step):         lift × 1
    """
    total = 0.0
    for s in shocks:
        if s["type"] != "shock":
            continue
        if s["start"] <= dt.date() <= s["end"]:
            duration = (s["end"] - s["start"]).days + 1
            t = (dt.date() - s["start"]).days
            p = t / duration if duration > 0 else 0
            shape = EVENT_MAPPING.get(s["shape"], "Step")
            if shape == "Step":
                total += s["str"]
            elif shape == "Linear Fade":
                total += s["str"] * (1 - p)
            elif shape == "Front-Loaded":
                total += s["str"] * np.exp(-3.0 * p)
            elif shape == "Delayed Peak":
                total += s["str"] * np.exp(
                    -((t - duration * 0.4) ** 2) / (2 * (duration * 0.3) ** 2)
                )
    return total


def _build_reapplied_cols(df, ev_subset):
    """Compute absolute and relative addition arrays from reapplied_shock events."""
    n = len(df)
    abs_s = np.zeros(n); abs_c = np.zeros(n); abs_r = np.zeros(n)
    rel_s = np.zeros(n); rel_c = np.zeros(n); rel_r = np.zeros(n)

    for ev in ev_subset:
        if ev["type"] != "reapplied_shock":
            continue
        new_end = ev["new_start"] + timedelta(days=ev["duration"] - 1)
        mask = (df["Date"].dt.date >= ev["new_start"]) & (df["Date"].dt.date <= new_end)
        idx  = df[mask].index
        k    = min(len(idx), ev["duration"])
        if ev["mode"] == "Absolute Volume":
            abs_s[idx[:k]] += np.array(ev["daily_abs_s"][:k])
            abs_c[idx[:k]] += np.array(ev["daily_abs_c"][:k])
            abs_r[idx[:k]] += np.array(ev["daily_abs_r"][:k])
        else:
            rel_s[idx[:k]] += np.array(ev["daily_pct_s"][:k])
            rel_c[idx[:k]] += np.array(ev["daily_pct_c"][:k])
            rel_r[idx[:k]] += np.array(ev["daily_pct_r"][:k])

    return abs_s, abs_c, abs_r, rel_s, rel_c, rel_r


def eval_events(ev_subset, *, pure_dna, adj_sessions, adj_conversions, adj_revenue,
                t_start, t_end, tgt_start, tgt_end):
    """Full simulation rebuild for an event subset (used by Attribution Engine).

    Returns {Revenue, Conversions, Sessions} totals for the target period.
    """
    from engine.dna import build_year_dataframe, build_dna_layers

    df, _ = build_year_dataframe(t_start.year)
    build_dna_layers(df, pure_dna, ev_subset)

    t_mask = (df["Date"].dt.date >= t_start) & (df["Date"].dt.date <= t_end)
    t_d    = df[t_mask]

    if t_d.empty or t_d["idx_sessions_pretrial"].sum() == 0:
        return {"Revenue": 0.0, "Conversions": 0.0, "Sessions": 0.0}

    b_sess = adj_sessions / t_d["idx_sessions_pretrial"].sum()
    t_cr   = adj_conversions / adj_sessions   if adj_sessions   > 0 else 0
    t_aov  = adj_revenue     / adj_conversions if adj_conversions > 0 else 0
    b_cr   = t_cr  / t_d["idx_cr_pretrial"].mean()  if t_d["idx_cr_pretrial"].mean()  > 0 else t_cr
    b_aov  = t_aov / t_d["idx_aov_pretrial"].mean() if t_d["idx_aov_pretrial"].mean() > 0 else t_aov

    df["Sessions_Base_"] = b_sess * df["idx_sessions_pretrial"]
    df["Conv_Base_"]     = df["Sessions_Base_"] * (b_cr  * df["idx_cr_pretrial"])
    df["Rev_Base_"]      = df["Conv_Base_"]      * (b_aov * df["idx_aov_pretrial"])

    df["Shock_"] = df["Date"].apply(lambda x: get_shock_multiplier(x, ev_subset))
    as_, ac, ar, rs, rc, rr = _build_reapplied_cols(df, ev_subset)

    s_std = (b_sess * df["idx_sessions_work"]) * (1 + df["Shock_"])
    c_std = s_std * (b_cr  * df["idx_cr_work"])
    r_std = c_std * (b_aov * df["idx_aov_work"])

    s_sim = s_std + df["Sessions_Base_"] * rs + as_
    c_sim = c_std + df["Conv_Base_"]     * rc + ac
    r_sim = r_std + df["Rev_Base_"]      * rr + ar

    tgt = (df["Date"].dt.date >= tgt_start) & (df["Date"].dt.date <= tgt_end)
    return {
        "Revenue":     float(r_sim[tgt].sum()),
        "Conversions": float(c_sim[tgt].sum()),
        "Sessions":    float(s_sim[tgt].sum()),
    }
