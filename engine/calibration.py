"""Calibration: anchor base constants to observed trial data, build projections."""
from engine.simulation import get_shock_multiplier, _build_reapplied_cols


def calibrate_base(df, t_start, t_end, adj_sessions, adj_conversions, adj_revenue):
    """Calibrate base constants from the pre-trial DNA and observed trial values.

    Formulae:
        base_sessions = adj_sessions / Σ(idx_sessions_pretrial over trial)
        base_CR       = (trial_CR) / mean(idx_cr_pretrial over trial)
        base_AOV      = (trial_AOV) / mean(idx_aov_pretrial over trial)

    Returns (base_sessions, base_cr, base_aov) or (None, None, None) on failure.
    """
    t_mask = (df["Date"].dt.date >= t_start) & (df["Date"].dt.date <= t_end)
    t_d    = df[t_mask]

    if t_d.empty or t_d["idx_sessions_pretrial"].sum() == 0:
        return None, None, None

    base_sessions = adj_sessions / t_d["idx_sessions_pretrial"].sum()
    trial_cr      = adj_conversions / adj_sessions    if adj_sessions    > 0 else 0
    trial_aov     = adj_revenue     / adj_conversions if adj_conversions > 0 else 0
    base_cr  = (trial_cr  / t_d["idx_cr_pretrial"].mean()
                if t_d["idx_cr_pretrial"].mean()  > 0 else trial_cr)
    base_aov = (trial_aov / t_d["idx_aov_pretrial"].mean()
                if t_d["idx_aov_pretrial"].mean() > 0 else trial_aov)

    return base_sessions, base_cr, base_aov


def build_projections(df, base_sessions, base_cr, base_aov, event_log):
    """Add Baseline, Simulation, and ±15% Margin columns to df in-place.

    Columns added:
        Sessions_Base, Conversions_Base, Revenue_Base   — baseline (pre-trial DNA, no shocks)
        Sessions_Sim,  Conversions_Sim,  Revenue_Sim    — simulation (work DNA + shocks)
        *_Base_Min, *_Base_Max, *_Sim_Min, *_Sim_Max    — ±15% confidence margins
    """
    # ── Baseline (pre-trial DNA, no shocks) ────────────────────────────────────
    df["Sessions_Base"]     = base_sessions * df["idx_sessions_pretrial"]
    df["Conversions_Base"]  = df["Sessions_Base"] * (base_cr  * df["idx_cr_pretrial"])
    df["Revenue_Base"]      = df["Conversions_Base"] * (base_aov * df["idx_aov_pretrial"])

    # ── Shock multiplier across the full year ──────────────────────────────────
    df["Shock"] = df["Date"].apply(lambda x: get_shock_multiplier(x, event_log))

    # ── Re-injected signature columns ──────────────────────────────────────────
    abs_s, abs_c, abs_r, rel_s, rel_c, rel_r = _build_reapplied_cols(df, event_log)

    # ── Simulation (work DNA + shocks + injections) ────────────────────────────
    s_standard = (base_sessions * df["idx_sessions_work"]) * (1 + df["Shock"])
    c_standard = s_standard * (base_cr  * df["idx_cr_work"])
    r_standard = c_standard * (base_aov * df["idx_aov_work"])

    df["Sessions_Sim"]    = s_standard + df["Sessions_Base"]    * rel_s + abs_s
    df["Conversions_Sim"] = c_standard + df["Conversions_Base"] * rel_c + abs_c
    df["Revenue_Sim"]     = r_standard + df["Revenue_Base"]     * rel_r + abs_r

    # ── Confidence margins ±15% ────────────────────────────────────────────────
    for m in ["Sessions", "Conversions", "Revenue"]:
        df[f"{m}_Base_Min"] = df[f"{m}_Base"] * 0.85
        df[f"{m}_Base_Max"] = df[f"{m}_Base"] * 1.15
        df[f"{m}_Sim_Min"]  = df[f"{m}_Sim"]  * 0.85
        df[f"{m}_Sim_Max"]  = df[f"{m}_Sim"]  * 1.15
