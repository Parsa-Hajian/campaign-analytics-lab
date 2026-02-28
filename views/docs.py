"""Documentation page: formulas, architecture, assumptions, and usage guide."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

_TMPL = "plotly_white"
_C_SIM = "#1a1a6b"


def _campaign_shape_fig():
    """Render the 4 campaign shape curves on a single figure."""
    duration = 30
    t = np.arange(duration)
    p = t / duration

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t, y=np.exp(-3.0 * p),
        name="Email Campaign (Front-Loaded)", line=dict(width=2.5, color="#F47920")))
    fig.add_trace(go.Scatter(
        x=t, y=1 - p,
        name="Flash Sale (Linear Fade)", line=dict(width=2.5, color="#10B981")))
    fig.add_trace(go.Scatter(
        x=t, y=np.exp(-((t - duration * 0.4) ** 2) / (2 * (duration * 0.3) ** 2)),
        name="Product Launch (Delayed Peak)", line=dict(width=2.5, color="#8B5CF6")))
    fig.add_trace(go.Scatter(
        x=t, y=np.ones(duration),
        name="Awareness Drive (Step)", line=dict(width=2.5, color="#EF4444")))

    fig.update_layout(
        template=_TMPL, height=300,
        title="Campaign Shape Functions (normalised lift over 30-day event)",
        xaxis_title="Days elapsed", yaxis_title="Lift multiplier (fraction of peak)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=50, b=0),
    )
    return fig


def render_docs():
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏗️ Architecture",
        "📐 Models & Formulas",
        "⚙️ Assumptions",
        "📊 Metric Selection Guide",
        "🚀 How to Use",
    ])

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 1: ARCHITECTURE
    # ─────────────────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("## Platform Architecture")
        st.markdown(
            "**Campaign Analytics Lab** is a decision-support platform for marketing and commercial teams. "
            "It combines historical demand modeling with forward-looking scenario simulation to answer:\n\n"
            "> *What should my business do organically, and what will my planned activities contribute?*"
        )

        st.markdown("---")
        st.markdown("### Three-Layer Model")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                "<div style='background:#EEF2FF;border-radius:10px;padding:16px 18px'>"
                "<div style='font-size:1.4rem'>🧬</div>"
                "<strong>Layer 1 — DNA</strong><br>"
                "<span style='font-size:0.85rem;color:#555'>Historical demand pattern modeling. "
                "Captures the seasonal shape of Sessions, CR, and AOV as normalized indices "
                "at monthly, weekly, and daily granularity.</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                "<div style='background:#F0FDF4;border-radius:10px;padding:16px 18px'>"
                "<div style='font-size:1.4rem'>🎯</div>"
                "<strong>Layer 2 — Calibration</strong><br>"
                "<span style='font-size:0.85rem;color:#555'>Anchors the model to current reality "
                "using a known trial period. Computes base constants (base_sessions, base_CR, base_AOV) "
                "that reconcile history with today's observations.</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                "<div style='background:#FFF7ED;border-radius:10px;padding:16px 18px'>"
                "<div style='font-size:1.4rem'>📈</div>"
                "<strong>Layer 3 — Simulation</strong><br>"
                "<span style='font-size:0.85rem;color:#555'>Projects full-year performance and "
                "applies campaign events (shocks, DNA adjustments, re-injections). "
                "Shows Before/After views with ±15% confidence bands.</span>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### Data Flow")
        st.code(
            """transactions.csv  (daily sessions / conversions / revenue per entity)
        │
        ▼
brand_profiles.csv  (pre-computed DNA indices — Monthly / Weekly / Daily)
        │
        ▼
[DNA Engine]  compute_similarity_weights()  →  35/65 blend  →  pure_dna
        │
        ▼
[Calibration]  calibrate_base()  →  base_sessions, base_CR, base_AOV
        │
        ▼
[Projection]  build_projections()  →  Baseline, Simulation, ±15% bands
        │
        ▼
Dashboard  ·  Lab  ·  Audit & Attribution""",
            language="text",
        )

        st.markdown("---")
        st.markdown("### Key Concepts")
        with st.expander("What is the DNA?"):
            st.markdown(
                "The **DNA (Demand Normalization Architecture)** is a set of normalized index series "
                "representing the *shape* of historical business performance. "
                "An index of **1.0** = the historical median for that time period. "
                "Values **> 1** indicate above-average periods; **< 1** indicate below-average.\n\n"
                "Three indices are tracked per period: **Sessions** (traffic demand), "
                "**CR** (conversion tendency), **AOV** (basket size tendency).\n\n"
                "The DNA allows the model to separate *amplitude* (calibrated to current observations) "
                "from *shape* (learned from history)."
            )
        with st.expander("What is calibration?"):
            st.markdown(
                "**Calibration** anchors the model to current reality. "
                "You provide observed metrics for a 'trial period' (a recent window of actual data). "
                "The engine computes base constants that, when multiplied by the historical DNA shape, "
                "reproduce those observed values — then extrapolates the full year.\n\n"
                "Think of calibration as telling the model: *'Here is what my business actually did. "
                "Now project forward using the historical shape.'*"
            )
        with st.expander("What is the 35/65 DNA blend?"):
            st.markdown(
                "The Pure DNA blends two signals:\n\n"
                "- **35% Overall** — the long-run median across all historical years\n"
                "- **65% Historical** — weighted average of per-year patterns\n\n"
                "The year weights are computed by **inverse similarity error**: "
                "years whose pattern was closest to your current trial period get higher weight. "
                "This makes the model adapt to changing business conditions year by year."
            )

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 2: MODELS & FORMULAS
    # ─────────────────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("## Models & Formulas")

        st.markdown("### 1. DNA Similarity Weights")
        st.info(
            "**Goal:** determine which historical year's pattern is most similar to the "
            "current trial period, so we can blend it more heavily."
        )
        st.code(
            """For each historical year i:
    err_i = ( |ΔSessions| + |ΔConversions| + |ΔRevenue| ) / 3
           where Δ = (observed_trial − historical_trial) / observed_trial

    w_i   = 1 / (err_i + 0.01)        ← inverse-error weight (ε=0.01 avoids ÷0)

    norm_w_i = w_i / Σ w_j             ← normalise to sum to 1""",
            language="text",
        )

        st.markdown("### 2. Pure DNA Construction")
        st.info("**Goal:** build the baseline monthly demand shape as a blended historical profile.")
        st.code(
            """For each calendar month t:

    Pure_DNA(t) = 0.35 × Overall_median(t)
                + 0.65 × Σᵢ [ norm_w_i × Year_i_median(t) ]

where Overall_median(t) is the median index across all years for month t,
and Year_i_median(t) is the median index for year i at month t.""",
            language="text",
        )

        st.markdown("### 3. Calibration")
        st.info("**Goal:** compute base constants from observed trial data.")
        st.code(
            """Given trial period [t_start, t_end] with observed:
    adj_sessions, adj_conversions, adj_revenue

base_sessions = adj_sessions / Σₜ( idx_sessions_pretrial(t) )
base_CR       = trial_CR  / mean( idx_cr_pretrial(t) )
base_AOV      = trial_AOV / mean( idx_aov_pretrial(t) )

where  trial_CR  = adj_conversions / adj_sessions
       trial_AOV = adj_revenue     / adj_conversions""",
            language="text",
        )

        st.markdown("### 4. Projections")
        st.info("**Goal:** produce full-year baseline and simulation forecasts.")
        st.code(
            """Baseline (no events — uses pre-trial DNA):
    Sessions(t)    = base_sessions × idx_sessions_pretrial(t)
    Conversions(t) = Sessions(t)   × base_CR  × idx_cr_pretrial(t)
    Revenue(t)     = Conversions(t) × base_AOV × idx_aov_pretrial(t)

Simulation (with events — uses work DNA + shocks):
    Sessions_sim(t)    = base_sessions × idx_sessions_work(t) × (1 + Shock(t))
    Conversions_sim(t) = Sessions_sim(t) × base_CR  × idx_cr_work(t)
    Revenue_sim(t)     = Conversions_sim(t) × base_AOV × idx_aov_work(t)

Confidence margins: ±15% on all projected values.""",
            language="text",
        )

        st.markdown("### 5. Campaign Shape Functions")
        st.markdown(
            "Each campaign event distributes its traffic lift over the campaign window "
            "according to a shape function. `p = days_elapsed / duration`  (0 → 1)."
        )
        st.plotly_chart(_campaign_shape_fig(), use_container_width=True)

        shapes_df = pd.DataFrame({
            "Shape":    ["Email Campaign", "Flash Sale", "Product Launch", "Awareness Drive"],
            "Type":     ["Front-Loaded", "Linear Fade", "Delayed Peak", "Step"],
            "Formula":  [
                "lift × e^(−3p)",
                "lift × (1 − p)",
                "lift × exp(−((t − 0.4d)² / (2(0.3d)²)))",
                "lift × 1",
            ],
            "Best for": [
                "Email blasts, push notifications",
                "Discount promotions, clearance sales",
                "New product launches, reveals",
                "Brand campaigns, outdoor, field activities",
            ],
        })
        st.dataframe(shapes_df, use_container_width=True, hide_index=True)

        st.markdown("### 6. De-Shock Isolation")
        st.info("**Goal:** separate the artificial (event-driven) component from the organic baseline.")
        st.code(
            """Given shock window [ds_start, ds_end]:

    floor = 10th percentile of sessions within [ds_start, ds_end]
          (conservative estimate of organic floor during the event)

    ΔSessions(t) = max(0, observed_sessions(t) − floor)

Organic CR  = floor_conversions / floor_sessions
Event CR    = ΔConversions.sum() / ΔSessions.sum()
CR Delta    = Event CR − Organic CR   (measures quality of event traffic)""",
            language="text",
        )

        st.markdown("### 7. Attribution Engine")
        st.info("**Goal:** measure the marginal contribution of each event to the target metric.")
        st.code(
            """For each event i in the active event list (in order):

    Contribution_i = metric(events[0..i]) − metric(events[0..i−1])
    Coverage_i (%) = Contribution_i / (Target − Organic_Base) × 100

This is a sequential 'leave-one-in' attribution:
events are credited in the order they were added.""",
            language="text",
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 3: ASSUMPTIONS
    # ─────────────────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("## Model Assumptions & Requirements")
        st.warning(
            "All quantitative models rely on assumptions. Understanding these helps you "
            "interpret results correctly and know when the model may be less reliable.")

        st.markdown("### Data Requirements")
        reqs = [
            ("Minimum history",  "At least **12 months** of daily data per entity for reliable DNA. "
                                 "2+ years recommended."),
            ("Metric consistency", "Your data must satisfy: **CR = Conversions ÷ Sessions** and "
                                   "**AOV = Revenue ÷ Conversions** consistently throughout."),
            ("Daily granularity", "The transactions file must have one row per entity per calendar day. "
                                  "The DNA system aggregates up to Monthly/Weekly/Daily resolutions."),
            ("Numeric stability", "Sessions should be > 0 for most days. Very sparse data (< 1 session/day "
                                  "on average) may produce unstable DNA indices."),
        ]
        for title, desc in reqs:
            st.markdown(f"**{title}:** {desc}")

        st.markdown("---")
        st.markdown("### Model Assumptions")

        assumptions = [
            ("1. Demand shape stationarity",
             "The seasonal pattern (shape) of Sessions, CR, and AOV is assumed stable across years. "
             "Only the amplitude can change. If your business underwent a structural break "
             "(e.g., entering a new market, major product pivot), the DNA from pre-break years "
             "may distort the model. Use the DNA similarity weights display to check: "
             "if one year has near-100% weight, earlier years are being discounted automatically."),
            ("2. Additive campaign effects",
             "Multiple campaign events are assumed to have **additive** effects on Sessions. "
             "In reality, overlapping campaigns may have diminishing returns (saturation) "
             "or amplifying effects (cross-channel synergy). The model does not model these interactions."),
            ("3. 10th-percentile organic floor",
             "In the De-Shock tool, the 10th percentile of Sessions within the shock window "
             "is used as the organic baseline. This is **conservative**: it assumes the lowest "
             "10% of traffic during the event period is organic. If events run for long periods, "
             "this may underestimate organic traffic. For short, sharp events (< 2 weeks) it works well."),
            ("4. ±15% uniform confidence margin",
             "All projections carry a ±15% uncertainty band. This is a heuristic and does not reflect "
             "actual statistical confidence intervals (which depend on data volume, noise level, and "
             "structural stability). Higher-noise businesses or shorter trial periods warrant wider margins."),
            ("5. Linear CR and AOV index scaling",
             "Conversion Rate and Average Order Value scale multiplicatively with their DNA indices. "
             "This implies that the CR and AOV shape is stable across time. "
             "In practice, CR often varies with acquisition channel mix, which is not modeled here."),
            ("6. Trial period representativeness",
             "The trial period you select should represent **normal business conditions**. "
             "Do not select a trial period that coincides with a major event (flash sale, "
             "seasonal peak) unless you use the Pre-Adjustment feature to strip the lift. "
             "An unrepresentative trial period will miscalibrate the entire projection."),
            ("7. No external confounder modeling",
             "The model does not account for: macroeconomic shocks, competitor actions, "
             "platform algorithm changes, data pipeline interruptions, or major holidays not "
             "already present in the historical pattern."),
            ("8. Revenue identity",
             "Revenue = Conversions × AOV is assumed throughout. "
             "If your revenue data includes non-conversion sources (subscriptions, returns refunded, "
             "etc.), the Revenue projections will be systematically biased."),
            ("9. Day-of-week effects at monthly resolution",
             "When using Monthly resolution, weekend suppression and weekday effects are averaged out. "
             "Switch to Daily resolution to capture day-of-week patterns explicitly."),
            ("10. Attribution is sequential, not causal",
             "The Attribution Engine assigns credit in the order events were added to the log. "
             "This is a sequential marginal contribution model, not a causal model. "
             "Reordering events will change individual contributions. "
             "For a more robust attribution, use Shapley-value averaging (not currently implemented)."),
        ]

        for title, desc in assumptions:
            with st.expander(title):
                st.markdown(desc)

        st.markdown("---")
        st.markdown("### Known Limitations")
        st.markdown(
            "- **No uncertainty propagation**: errors in calibration inputs are not propagated "
            "to the confidence bands.\n"
            "- **No channel-level granularity**: the model operates at entity level, "
            "not channel level (paid search vs. organic vs. email).\n"
            "- **No competitor modeling**: market share shifts are not captured.\n"
            "- **DNA computed at monthly granularity for projections**: even at Weekly/Daily resolution "
            "display, the baseline DNA is always blended monthly for the core projection.\n"
            "- **Re-injection signatures are entity-aggregated**: the de-shock tool "
            "aggregates across selected entities, not per-entity."
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 4: METRIC SELECTION GUIDE
    # ─────────────────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("## Metric Selection Guide")
        st.markdown(
            "For the model to work correctly, your three core metrics must satisfy "
            "a set of coherence conditions. This guide helps you choose correctly."
        )

        st.markdown("### The Three Core Metrics")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                "<div style='background:#EEF2FF;border-radius:8px;padding:14px'>"
                "<strong>Sessions</strong><br>"
                "<span style='font-size:0.85rem;color:#555'>"
                "Your primary <b>traffic / demand volume</b> metric. "
                "This is the numerator in the CR calculation. "
                "Should respond to campaign activity.<br><br>"
                "<em>Examples: website sessions, store visits, app opens, "
                "ad impressions (awareness campaigns), email deliveries.</em>"
                "</span></div>",
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                "<div style='background:#F0FDF4;border-radius:8px;padding:14px'>"
                "<strong>Conversions</strong><br>"
                "<span style='font-size:0.85rem;color:#555'>"
                "Your primary <b>conversion action</b>. "
                "The denominator in AOV and numerator of CR.<br><br>"
                "<em>Examples: purchases, leads submitted, sign-ups, "
                "qualified appointments, units sold.</em>"
                "</span></div>",
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                "<div style='background:#FFF7ED;border-radius:8px;padding:14px'>"
                "<strong>Revenue</strong><br>"
                "<span style='font-size:0.85rem;color:#555'>"
                "The monetary value of your conversions. "
                "Must equal Conversions × AOV within acceptable tolerance.<br><br>"
                "<em>Examples: gross sales, net revenue, contract value, "
                "subscription MRR.</em>"
                "</span></div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### Coherence Checklist")
        st.success(
            "Before entering data, verify these identities hold in your dataset "
            "within ±5% tolerance:")
        st.code(
            """CR  = Conversions / Sessions     (e.g. 100 purchases / 5,000 visits = 2.0% CR)
AOV = Revenue / Conversions       (e.g. €10,000 revenue / 100 purchases = €100 AOV)
Revenue = Sessions × CR × AOV     (the fundamental identity)""",
            language="text",
        )

        st.markdown("---")
        st.markdown("### Choosing the Right Trial Period")
        with st.expander("What is a trial period?"):
            st.markdown(
                "The **trial period** is a recent window of actual data you give the model "
                "to anchor its projections. You enter three numbers: total Sessions, "
                "Conversions, and Revenue for that period.\n\n"
                "The model uses these to compute `base_sessions`, `base_CR`, and `base_AOV`, "
                "which scale the historical DNA to produce current-level projections."
            )
        with st.expander("Good vs. bad trial periods"):
            good_col, bad_col = st.columns(2)
            with good_col:
                st.markdown("**Good trial periods:**")
                st.markdown(
                    "- Recent (last 1–3 months)\n"
                    "- Representative of normal operations\n"
                    "- No major events or anomalies\n"
                    "- At least 7 days (ideally 14–30)\n"
                    "- Fully closed (data is complete)"
                )
            with bad_col:
                st.markdown("**Avoid as trial periods:**")
                st.markdown(
                    "- Periods with major campaigns running\n"
                    "- Black Friday / holiday peak\n"
                    "- Outage or data gaps\n"
                    "- Only 1–2 days\n"
                    "- Future dates (no actual data)"
                )
        with st.expander("Using the Pre-Adjustment"):
            st.markdown(
                "If your best available trial period had a known event (e.g., a 30% traffic boost "
                "from an email campaign), use the **Pre-Adjustment** slider:\n\n"
                "- Enter `+30%` in 'Sessions adj (%)' to strip the lift.\n"
                "- The model divides your observed sessions by 1.30, calibrating to the organic base.\n\n"
                "Formula: `adj_sessions = raw_sessions / (1 + adj_pct / 100)`\n\n"
                "A **positive** adjustment means the trial was inflated → strip lift.\n"
                "A **negative** adjustment means the trial was suppressed → add lift back."
            )

        st.markdown("---")
        st.markdown("### When Metrics Behave Unexpectedly")
        issues = {
            "CR is very high (> 20%)":
                "Check that Sessions and Conversions use the same definition. "
                "If Sessions = add-to-cart events and Conversions = purchases, "
                "CR will be inflated vs. site-wide CR. Use consistent definitions.",
            "AOV varies wildly by month":
                "High AOV volatility may indicate mix shifts (product category changes, "
                "currency effects). The DNA AOV index will capture this shape, "
                "but consider whether it's structural or noise.",
            "Revenue doesn't match Sessions × CR × AOV":
                "Revenue may include subscription revenue, returns/refunds, "
                "or currency conversion effects. Ensure your Revenue column "
                "is the gross transaction value from conversions only.",
            "DNA weights show 100% on one year":
                "One year dominates because it was most similar to your trial period. "
                "This is normal if that year had a very similar seasonal pattern. "
                "If it seems wrong, check your trial period dates.",
            "Baseline projection seems too high/low":
                "Re-check your trial period: total Sessions, Conversions, Revenue "
                "must match what actually happened in those dates. "
                "Also verify the Pre-Adjustment is set correctly.",
        }
        for issue, solution in issues.items():
            with st.expander(f"⚠️ {issue}"):
                st.markdown(solution)

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 5: HOW TO USE
    # ─────────────────────────────────────────────────────────────────────────────
    with tab5:
        st.markdown("## Complete Usage Guide")
        st.info(
            "Follow these steps in order for your first session. "
            "After that, steps 1–3 (data, sidebar, calibration) are usually pre-configured "
            "and you can go straight to simulation.")

        # ── STEP 1 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 1 — Prepare Your Data")
        st.markdown(
            "Place your CSV files in the `data/` folder before launching the app.\n\n"
            "**Option A — Use the synthetic demo data** (already in `data/`): no action needed.\n\n"
            "**Option B — Use your own data:**\n"
            "1. Create `data/transactions.csv` with columns: "
            "`Date, brand, sessions, conversions, revenue, cr, aov`\n"
            "2. Run `python generate_data.py` to auto-generate `brand_profiles.csv` "
            "and `yearly_kpis.csv` from your transactions file.\n"
            "3. Restart the app.\n\n"
            "See the `generate_data.py` script for the expected column formats."
        )
        with st.expander("Column format reference"):
            schema = pd.DataFrame({
                "Column":      ["Date", "brand", "sessions", "conversions", "revenue", "cr", "aov", "campaign", "campaign_volume"],
                "Type":        ["YYYY-MM-DD", "string", "int", "int", "float", "float (0–1)", "float", "string", "string"],
                "Description": [
                    "Calendar date",
                    "Entity identifier (lowercase)",
                    "Total sessions / visits for that day",
                    "Total conversions (purchases, leads, etc.)",
                    "Total revenue from conversions",
                    "CR = conversions / sessions",
                    "AOV = revenue / conversions",
                    "'yes'/'no' — whether a campaign ran that day",
                    "Campaign type label (or 'no-campaign')",
                ],
            })
            st.dataframe(schema, use_container_width=True, hide_index=True)

        # ── STEP 2 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 2 — Launch & Log In")
        st.code("streamlit run app.py", language="bash")
        st.markdown(
            "Open your browser at `http://localhost:8501`. "
            "Log in with your credentials. "
            "For the demo app, use: **username = `demo`**, **password = `demo2026`**."
        )

        # ── STEP 3 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 3 — Configure the Sidebar")
        st.markdown(
            "The sidebar controls the model for the entire session:\n\n"
            "**Market Resolution** — choose Monthly, Weekly, or Daily. "
            "Monthly is fastest and best for strategic planning; "
            "Daily gives the most granular view.\n\n"
            "**Entities (Brands)** — select which entities to include. "
            "Multi-entity selection blends their DNA profiles. "
            "Single-entity mode unlocks the Goal Tracker's historical chart.\n\n"
            "**Trial Reality** — enter your observed actual numbers:\n"
            "- Start Date / End Date: the period for which you have complete actual data\n"
            "- Sessions: total sessions during that period\n"
            "- Conversions: total conversions\n"
            "- Revenue: total revenue\n\n"
            "**Pre-Adjustment (optional)** — if the trial period was affected by "
            "an event, adjust by the estimated lift % to compute the organic base.\n\n"
            "**DNA Weights** — after entering trial data, the sidebar shows how "
            "much weight each historical year gets. 35% goes to all-time overall; "
            "65% is distributed across years by similarity to your trial period."
        )

        # ── STEP 4 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 4 — Dashboard: Projection Overview")
        st.markdown(
            "Navigate to **📊 Dashboard** → **📈 Projection Overview**.\n\n"
            "- Select a metric (Revenue, Sessions, Conversions, CR, AOV)\n"
            "- The chart shows the **Baseline** (organic, no campaigns) "
            "with ±15% confidence bands\n"
            "- As you add events in the Lab, a second **Forecast** line appears "
            "showing the simulated outcome\n"
            "- Shaded windows mark campaign periods\n\n"
            "**Tip:** if the baseline looks wrong (too high or too low), "
            "return to the sidebar and check your Trial Reality values."
        )

        # ── STEP 5 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 5 — Dashboard: Goal Tracker")
        st.markdown(
            "Navigate to **📊 Dashboard** → **🎯 Goal Tracker**.\n\n"
            "1. **(Single entity only)** Select a historical year and growth % "
            "to compute a target automatically\n"
            "2. Set your **Target Period** (the future window you're planning for)\n"
            "3. Select your **Target Metric** (Revenue, Conversions, Sessions, CR, or AOV)\n"
            "4. Choose the **Volume Driver**: how will you achieve the target? "
            "Via more traffic, higher CR, or higher AOV?\n"
            "5. Review the **KPI Matrix**: what's needed vs. what the baseline delivers\n"
            "6. Add campaigns in the Lab (Step 7) and return here "
            "to see if the gap closes\n\n"
            "**Gap charts** show period-by-period surplus (+) or shortfall (−) vs. target."
        )

        # ── STEP 6 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 6 — Dashboard: DNA Profile")
        st.markdown(
            "Navigate to **📊 Dashboard** → **🧬 Demand DNA Profile**.\n\n"
            "This shows the seasonal index patterns for Sessions (orange), "
            "CR (teal), and AOV (violet) across the selected time resolution.\n\n"
            "**Three layers:**\n"
            "- **Pure** (dashed, light): raw blended historical shape\n"
            "- **Pre-Trial** (dashed, medium): after any Pre-Trial DNA edits\n"
            "- **Work** (solid, bold): final projected shape after all modifications\n\n"
            "Use this to understand **when** your business naturally peaks and troughs "
            "before planning campaign timing."
        )

        # ── STEP 7 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 7 — Simulation Lab: Campaigns (Events Tab)")
        st.markdown(
            "Navigate to **⚡ Lab** → **🚀 Events**.\n\n"
            "**To add a campaign:**\n"
            "1. Select Start and End dates for the campaign window\n"
            "2. Choose a Campaign Shape (see Step 9 for guidance)\n"
            "3. Set the **Traffic Lift (%)**: estimated sessions increase vs. baseline\n"
            "   - Default is loaded from Settings; override as needed\n"
            "   - Use historical de-shock data (Step 9) for evidence-based lift estimates\n"
            "4. Click **Inject Campaign**\n\n"
            "The campaign immediately appears in all Dashboard charts. "
            "Repeat for multiple campaigns.\n\n"
            "**Swap DNA:** the right-hand column lets you swap the demand profile "
            "of two time periods (e.g., swap January and July demand shapes). "
            "Choose Pre-Trial to affect calibration, or Post-Trial for projection only."
        )

        # ── STEP 8 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 8 — Simulation Lab: DNA Drag")
        st.markdown(
            "Navigate to **⚡ Lab** → **🖱️ Visual DNA Drag**.\n\n"
            "This lets you **sculpt the demand shape** for a specific time period:\n"
            "1. Click a point on the chart to select a period\n"
            "2. Set the Multiplier (× 1.0 = no change, × 2.0 = double that period's index)\n"
            "3. Choose Pre-Trial or Post-Trial scope\n"
            "4. Click Apply\n\n"
            "**Use case:** you know that a new product launch will shift your "
            "typical November peak to October. Drag October's multiplier up and "
            "November's down to model this structural change."
        )

        # ── STEP 9 ────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 9 — Simulation Lab: De-Shock Tool")
        st.markdown(
            "Navigate to **⚡ Lab** → **🧹 De-Shock Tool**.\n\n"
            "Use this to **extract the incremental effect** of a past campaign from historical data:\n"
            "1. Pick a date window where you know a campaign ran\n"
            "2. Review the forensic chart: organic floor (10th percentile) is shown as a red dashed line\n"
            "3. The green area above the floor = the extracted shock (artificial demand)\n"
            "4. Review metrics: Δ Sessions, Δ Conversions, Δ Revenue, Event CR vs. Organic CR\n"
            "5. Name and **Save to Library**\n\n"
            "**Signature Library:** once saved, you can **re-inject** the signature "
            "into any future date. Two injection modes:\n"
            "- **Absolute Volume**: replays the exact historical daily increments\n"
            "- **Relative Baseline Multiplier**: scales the increments to the current "
            "forecast baseline (recommended when scale has changed year-over-year)"
        )

        # ── STEP 10 ───────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 10 — Simulation Lab: Audit & Attribution")
        st.markdown(
            "Navigate to **⚡ Lab** → **📋 Audit & Gap Attribution**.\n\n"
            "This shows every active event and its **marginal contribution** to the "
            "target metric set in the Goal Tracker:\n\n"
            "- Each event shows: metric delta (absolute) and gap coverage (%)\n"
            "- Events with negative delta are reducing your target metric "
            "(e.g., a swap that moved demand away from the target period)\n"
            "- **Shift (↔)**: move a campaign to a different start date without re-entering it\n"
            "- **Delete (❌)**: remove an event\n"
            "- **Clear All**: reset the simulation\n\n"
            "**Attribution note:** events are credited sequentially in the order added. "
            "To test sensitivity, add events in different orders."
        )

        # ── STEP 11 ───────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 11 — Settings")
        st.markdown(
            "Navigate to **⚙️ Settings**.\n\n"
            "Set the **default Traffic Lift (%)** for each campaign shape per entity. "
            "These defaults pre-populate the slider in the Events tab when you select a shape, "
            "saving time across repeated planning sessions.\n\n"
            "- Use the table to set per-entity overrides\n"
            "- The **Apply Global to All Entities** button copies the 'Global Default' row "
            "to all entities at once\n"
            "- Click **Save Settings** to persist (settings are saved to `data/settings.json`)"
        )

        # ── STEP 12 ───────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Step 12 — Export")
        st.markdown(
            "In the sidebar, click **Download Strategy Report**.\n\n"
            "This generates an Excel file with:\n"
            "- Full-year daily projections (Baseline + Simulation for all metrics)\n"
            "- Summary KPI table\n"
            "- Active event log\n\n"
            "Share with stakeholders who don't have access to the app."
        )

        # ── TIPS ──────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Tips & Best Practices")
        tips = [
            ("Start with one entity",
             "Multi-entity DNA blending is powerful but harder to interpret. "
             "Master the model on a single entity first, then explore combined views."),
            ("Use Monthly resolution for strategy, Daily for execution",
             "Monthly is faster, less noisy, and better for Q-level planning. "
             "Switch to Daily when scheduling specific campaign dates."),
            ("Calibrate on a quiet period",
             "A 2–4 week period with no major campaigns, no anomalies, and complete data "
             "gives the most reliable calibration. January is often good for seasonal businesses."),
            ("Test campaign timing by shifting events",
             "Use the Shift (↔) button to move a campaign window and instantly see "
             "if an earlier or later date gives better goal coverage."),
            ("Build a de-shock library before planning",
             "Before your annual planning cycle, extract shock signatures for your "
             "key recurring events (Black Friday, summer sale, product launch). "
             "Then re-inject them to model next year."),
            ("Review DNA weights each session",
             "The sidebar shows DNA weights. If one year dominates (> 80%), "
             "check if that year really was most similar to your current period. "
             "If not, your trial dates or values may need adjustment."),
        ]
        for title, desc in tips:
            with st.expander(f"💡 {title}"):
                st.markdown(desc)
