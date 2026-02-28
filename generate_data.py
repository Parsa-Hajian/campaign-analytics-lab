"""
Synthetic dataset generator for Campaign Analytics Lab.
Run this script once to produce the three CSV files in data/.

Usage:
    python generate_data.py

Output:
    data/transactions.csv      — daily records per entity
    data/brand_profiles.csv    — pre-computed DNA indices (Monthly/Weekly/Daily)
    data/yearly_kpis.csv       — annual KPI aggregates per entity
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)

# ── Entity definitions ──────────────────────────────────────────────────────────
# Five synthetic entities with distinct business patterns.
# Seasonal weights: [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
ENTITIES = {
    "alpha": {
        "label":    "Alpha (Tech)",
        "base_sessions": 80,
        "base_cr":       0.0050,   # 0.5%
        "base_aov":      420.0,
        "seasonal":  [0.70, 0.75, 0.85, 0.90, 0.95, 0.85, 0.75, 0.80, 0.90, 1.10, 1.40, 1.60],
        "growth":    0.12,         # 12% YoY
    },
    "beta": {
        "label":    "Beta (Retail)",
        "base_sessions": 350,
        "base_cr":       0.0180,   # 1.8%
        "base_aov":      95.0,
        "seasonal":  [0.80, 0.75, 1.05, 1.15, 1.00, 0.85, 0.75, 0.80, 0.95, 1.20, 1.45, 1.55],
        "growth":    0.08,
    },
    "gamma": {
        "label":    "Gamma (Luxury)",
        "base_sessions": 25,
        "base_cr":       0.0020,   # 0.2%
        "base_aov":      1100.0,
        "seasonal":  [0.60, 0.65, 1.10, 1.30, 1.20, 0.85, 0.65, 0.70, 0.80, 0.95, 1.25, 1.40],
        "growth":    0.05,
    },
    "delta": {
        "label":    "Delta (FMCG)",
        "base_sessions": 600,
        "base_cr":       0.0300,   # 3%
        "base_aov":      35.0,
        "seasonal":  [0.90, 0.88, 0.92, 0.95, 1.05, 1.10, 1.15, 1.10, 1.05, 0.95, 0.90, 0.85],
        "growth":    0.06,
    },
    "epsilon": {
        "label":    "Epsilon (B2B)",
        "base_sessions": 35,
        "base_cr":       0.0012,   # 0.12%
        "base_aov":      3200.0,
        "seasonal":  [1.30, 1.20, 1.10, 0.90, 0.85, 0.80, 1.20, 1.15, 1.10, 0.95, 0.80, 0.70],
        "growth":    0.15,
    },
}

# Weekend suppression (Sat/Sun have lower sessions for most B2C entities)
DOW_FACTORS = [1.05, 1.05, 1.00, 1.00, 1.05, 0.80, 0.75]

START_DATE = "2022-01-01"
END_DATE   = "2025-10-31"


# ── Transaction generation ───────────────────────────────────────────────────────

def build_transactions() -> pd.DataFrame:
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    rows  = []

    for d in dates:
        month_idx = d.month - 1
        dow_idx   = d.dayofweek
        for brand, cfg in ENTITIES.items():
            year_factor = (1 + cfg["growth"]) ** (d.year - 2022)
            seasonal    = cfg["seasonal"][month_idx]
            dow_f       = DOW_FACTORS[dow_idx]

            # Log-normal noise keeps values positive and realistic
            s_noise  = np.random.lognormal(0, 0.18)
            cr_noise = np.random.lognormal(0, 0.12)
            aov_noise= np.random.lognormal(0, 0.09)

            sessions    = max(0.0, cfg["base_sessions"] * year_factor * seasonal * dow_f * s_noise)
            cr          = min(0.25, max(0.0001, cfg["base_cr"] * cr_noise))
            aov         = max(5.0,  cfg["base_aov"] * aov_noise)
            # Poisson sampling handles low-volume entities correctly
            expected_conv = sessions * cr
            conversions   = int(np.random.poisson(expected_conv)) if expected_conv > 0 else 0
            revenue       = round(conversions * aov, 2)

            rows.append({
                "Date":             d.date(),
                "brand":            brand,
                "sessions":         round(sessions),
                "conversions":      conversions,
                "revenue":          revenue,
                "cr":               round(cr, 6),
                "aov":              round(aov, 2),
                "campaign":         "no",
                "campaign_volume":  "no-campaign",
            })

    return pd.DataFrame(rows)


# ── Profile computation ─────────────────────────────────────────────────────────

def _idx(series: pd.Series) -> pd.Series:
    """Normalize to median = 1. Returns 1.0 if median is zero."""
    med = series.median()
    return (series / med).fillna(1.0) if med > 0 else pd.Series(1.0, index=series.index)


def build_profiles(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Year"]      = df["Date"].dt.year.astype(str)
    df["Month"]     = df["Date"].dt.month
    df["Week"]      = df["Date"].dt.isocalendar().week.astype(int)
    df["DayOfYear"] = df["Date"].dt.dayofyear

    parts = []

    for brand in ENTITIES:
        bdf = df[df["brand"] == brand]
        years = [("Overall", bdf)] + [
            (y, bdf[bdf["Year"] == y]) for y in sorted(bdf["Year"].unique())
        ]

        for year_label, ydf in years:
            if ydf.empty:
                continue

            for level, t_col in [("Monthly", "Month"), ("Weekly", "Week"), ("Daily", "DayOfYear")]:
                agg = (
                    ydf.groupby(t_col)
                    .agg(sessions=("sessions", "sum"),
                         conversions=("conversions", "sum"),
                         revenue=("revenue", "sum"))
                    .reset_index()
                    .rename(columns={t_col: "TimeIdx"})
                )
                agg["cr"]  = agg["conversions"] / agg["sessions"].replace(0, float("nan"))
                agg["aov"] = agg["revenue"]      / agg["conversions"].replace(0, float("nan"))
                agg = agg.fillna(0)

                agg["idx_sessions"] = _idx(agg["sessions"]).values
                agg["idx_cr"]       = _idx(agg["cr"]).values
                agg["idx_aov"]      = _idx(agg["aov"]).values

                agg["brand"]   = brand
                agg["Level"]   = level
                agg["Year"]    = year_label
                agg["level_1"] = agg["TimeIdx"] - 1

                parts.append(agg[[
                    "brand", "level_1", "TimeIdx",
                    "sessions", "conversions", "revenue",
                    "cr", "aov",
                    "idx_sessions", "idx_cr", "idx_aov",
                    "Level", "Year",
                ]])

    return pd.concat(parts, ignore_index=True)


# ── Yearly KPIs ─────────────────────────────────────────────────────────────────

def build_yearly_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Year"] = df["Date"].dt.year

    rows = []
    for brand in ENTITIES:
        bdf = df[df["brand"] == brand]
        for year in sorted(bdf["Year"].unique()):
            ydf  = bdf[bdf["Year"] == year]
            s    = ydf["sessions"].sum()
            c    = ydf["conversions"].sum()
            r    = ydf["revenue"].sum()
            rows.append({
                "brand":       brand,
                "Year":        year,
                "sessions":    round(s),
                "conversions": round(c),
                "revenue":     round(r, 2),
                "cr":          round(c / s if s > 0 else 0, 6),
                "aov":         round(r / c if c > 0 else 0, 2),
            })
    return pd.DataFrame(rows)


# ── Main ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    print("Generating transactions…")
    trans = build_transactions()
    trans.to_csv("data/transactions.csv", index=False)
    print(f"  → data/transactions.csv  ({len(trans):,} rows)")

    print("Building brand profiles…")
    profiles = build_profiles(trans)
    profiles.to_csv("data/brand_profiles.csv", index=False)
    print(f"  → data/brand_profiles.csv  ({len(profiles):,} rows)")

    print("Building yearly KPIs…")
    kpis = build_yearly_kpis(trans)
    kpis.to_csv("data/yearly_kpis.csv", index=False)
    print(f"  → data/yearly_kpis.csv  ({len(kpis):,} rows)")

    print("\nDone. Summary:")
    for brand, cfg in ENTITIES.items():
        sub = trans[trans["brand"] == brand]
        print(
            f"  {brand:8s}  sessions={sub['sessions'].sum():>10,.0f}  "
            f"revenue=€{sub['revenue'].sum():>12,.0f}"
        )
