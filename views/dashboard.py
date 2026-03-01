"""Main dashboard: Projection Overview, Goal Tracker, DNA Profile."""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from utils.fmt import _fmt, color_neg

_C_BASE   = "#94a3b8"
_C_SIM    = "#1a1a6b"
_C_BAND   = "rgba(26,26,107,0.12)"
_C_TARGET = "#dc2626"
_C_SHOCK  = "rgba(220,38,38,0.10)"
_TEMPLATE = "plotly_white"


def _add_shock_markers(fig, event_log):
    for ev in event_log:
        if ev["type"] == "shock":
            fig.add_vrect(
                x0=str(ev["start"]), x1=str(ev["end"]),
                fillcolor=_C_SHOCK, layer="below", line_width=0,
                annotation_text=f"📣 {ev.get('shape','')[:12]}",
                annotation_position="top left",
                annotation=dict(font_size=10, font_color="#dc2626"),
            )
        elif ev["type"] == "reapplied_shock":
            from datetime import timedelta
            end_d = ev["new_start"] + timedelta(days=ev["duration"] - 1)
            fig.add_vrect(
                x0=str(ev["new_start"]), x1=str(end_d),
                fillcolor="rgba(16,185,129,0.10)", layer="below", line_width=0,
                annotation_text="💉", annotation_position="top left",
                annotation=dict(font_size=10),
            )


def render_dashboard(df, profiles, yearly_kpis, sel_brands, res_level, time_col,
                     base_cr, base_aov):
    if "event_log"     not in st.session_state: st.session_state.event_log     = []
    if "tgt_start"     not in st.session_state: st.session_state.tgt_start     = None
    if "tgt_end"       not in st.session_state: st.session_state.tgt_end       = None
    if "target_metric" not in st.session_state: st.session_state.target_metric = "Revenue"
    if "target_val"    not in st.session_state: st.session_state.target_val    = 0.0

    event_log  = st.session_state.event_log
    has_events = bool(event_log)

    tab1, tab2, tab3 = st.tabs([
        "📈 Projection Overview",
        "🎯 Goal Tracker",
        "🧬 Demand DNA Profile",
    ])

    # ── Tab 1: Projection Overview ──────────────────────────────────────────────
    with tab1:
        agg_cols = {
            "Date": "first",
            **{
                f"{m}_{v}": "sum"
                for m in ["Sessions", "Conversions", "Revenue"]
                for v in ["Base", "Sim", "Base_Min", "Base_Max", "Sim_Min", "Sim_Max"]
            },
        }
        agg_df = df.groupby(time_col).agg(agg_cols).reset_index()

        for pfx in ["_Base", "_Sim", "_Base_Min", "_Base_Max", "_Sim_Min", "_Sim_Max"]:
            agg_df[f"CR{pfx}"] = (
                (agg_df[f"Conversions{pfx}"] / agg_df[f"Sessions{pfx}"])
                .replace([float("inf"), float("-inf")], 0).fillna(0)
            )
            agg_df[f"AOV{pfx}"] = (
                (agg_df[f"Revenue{pfx}"] / agg_df[f"Conversions{pfx}"])
                .replace([float("inf"), float("-inf")], 0).fillna(0)
            )

        met = st.selectbox("Select Metric", ["Revenue", "Sessions", "Conversions", "CR", "AOV"])
        fig = go.Figure()

        if has_events:
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Base_Max"],
                mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Base_Min"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor="rgba(148,163,184,0.15)",
                name="±15% Baseline Band"))
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Base"],
                mode="lines", line=dict(color=_C_BASE, dash="dot", width=2),
                name="Baseline (No Events)"))
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Sim_Max"],
                mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Sim_Min"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor=_C_BAND, name="±15% Forecast Band"))
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Sim"],
                mode="lines+markers", line=dict(color=_C_SIM, width=3),
                name="Forecast (With Events)"))
            _add_shock_markers(fig, event_log)
        else:
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Base_Max"],
                mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Base_Min"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor="rgba(148,163,184,0.15)", name="±15% Range"))
            fig.add_trace(go.Scatter(
                x=agg_df["Date"], y=agg_df[f"{met}_Base"],
                mode="lines+markers", line=dict(color=_C_BASE, width=3),
                name="Baseline"))

        fig.update_layout(
            template=_TEMPLATE,
            title=dict(text=f"{res_level} Forecast — {met}", font=dict(size=18, color="#12124a")),
            xaxis_title="Date", yaxis_title=met,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
        if has_events:
            st.caption(
                f"**{len(event_log)} event(s)** active — shaded bands show campaign windows. "
                "Manage in ⚡ Lab → 📋 Audit.")

    # ── Tab 3: Demand DNA Profile ────────────────────────────────────────────────
    # NOTE: processed before Tab 2 so early-return in Goal Tracker cannot block DNA Profile.
    with tab3:
        st.subheader("Current Operational DNA")
        st.caption(
            "Three layers: **Pure** (historical blend) · **Pre-Trial** (calibration state) · "
            "**Work** (final projection state after all modifications)")

        dna_plot = df.groupby(time_col).agg({
            "idx_sessions_pure": "mean", "idx_cr_pure": "mean", "idx_aov_pure": "mean",
            "idx_sessions_pretrial": "mean", "idx_cr_pretrial": "mean", "idx_aov_pretrial": "mean",
            "idx_sessions_work": "mean", "idx_cr_work": "mean", "idx_aov_work": "mean",
        }).reset_index()

        _DNA_PURE     = [("#FCD34D", "Sessions"), ("#6EE7B7", "CR"), ("#C4B5FD", "AOV")]
        _DNA_PRETRIAL = [("#F97316", "Sessions"), ("#10B981", "CR"), ("#8B5CF6", "AOV")]
        _DNA_WORK     = [("#C2410C", "Sessions"), ("#065F46", "CR"), ("#5B21B6", "AOV")]
        _DNA_COLS_P   = ["idx_sessions_pure",    "idx_cr_pure",    "idx_aov_pure"]
        _DNA_COLS_PT  = ["idx_sessions_pretrial", "idx_cr_pretrial", "idx_aov_pretrial"]
        _DNA_COLS_W   = ["idx_sessions_work",     "idx_cr_work",     "idx_aov_work"]

        fig_dna = go.Figure()
        for col, (color, name) in zip(_DNA_COLS_P, _DNA_PURE):
            fig_dna.add_trace(go.Scatter(
                x=dna_plot[time_col], y=dna_plot[col],
                mode="lines", line=dict(dash="dot", width=2, color=color),
                name=f"{name} (Pure)"))

        if has_events:
            for col, (color, name) in zip(_DNA_COLS_PT, _DNA_PRETRIAL):
                fig_dna.add_trace(go.Scatter(
                    x=dna_plot[time_col], y=dna_plot[col],
                    mode="lines", line=dict(dash="dash", width=2.5, color=color),
                    name=f"{name} (Pre-Trial)"))
            for col, (color, name) in zip(_DNA_COLS_W, _DNA_WORK):
                fig_dna.add_trace(go.Scatter(
                    x=dna_plot[time_col], y=dna_plot[col],
                    mode="lines+markers",
                    line=dict(width=3.5, color=color), marker=dict(size=5, color=color),
                    name=f"{name} (Work)"))

        fig_dna.update_layout(
            template=_TEMPLATE,
            title=dict(text=f"DNA Profile — {res_level} Resolution", font=dict(color="#12124a")),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Index (1.0 = historical median)",
        )
        st.plotly_chart(fig_dna, use_container_width=True)

        if has_events:
            dna_evs = [e for e in event_log if e["type"] in ("custom_drag", "swap")]
            if dna_evs:
                st.markdown(
                    f"**{len(dna_evs)} DNA modification(s) active** — manage in ⚡ Lab → 📋 Audit")

    # ── Tab 2: Goal Tracker ─────────────────────────────────────────────────────
    with tab2:
        st.subheader("🎯 Target Translation")
        calculated_target = st.session_state.target_val
        target_metric_raw = "revenue"
        metric_map = {
            "revenue": "Revenue", "conversions": "Conversions", "sessions": "Sessions",
            "cr": "CR", "aov": "AOV",
        }

        if len(sel_brands) == 1:
            st.info(f"📈 **Single Entity Mode:** {sel_brands[0].title()}")
            brand_hist = yearly_kpis[yearly_kpis["brand"] == sel_brands[0]].sort_values("Year")

            h1, h2, h3 = st.columns(3)
            hist_year         = h1.selectbox("Base Year", brand_hist["Year"].unique())
            target_metric_raw = h2.selectbox(
                "Historical Metric", ["revenue", "conversions", "sessions", "cr", "aov"])
            growth_pct        = h3.number_input("Growth vs Year (%)", value=5.0, step=1.0)

            fig_h = px.bar(
                brand_hist, x="Year", y=target_metric_raw,
                title=f"Historical {metric_map[target_metric_raw]}",
                text_auto=".2s", color_discrete_sequence=["#1a1a6b"],
            )
            fig_h.update_layout(template=_TEMPLATE, height=300)
            c_ch, c_tb = st.columns([2, 1])
            with c_ch:
                st.plotly_chart(fig_h, use_container_width=True)
            with c_tb:
                fmt_s = (
                    "{:.2%}"   if target_metric_raw == "cr"
                    else "€{:,.2f}" if target_metric_raw == "aov"
                    else "{:,.0f}"
                )
                st.dataframe(
                    brand_hist[["Year", target_metric_raw]]
                    .style.format({target_metric_raw: fmt_s}),
                    use_container_width=True, hide_index=True,
                )

            base_hist = brand_hist[brand_hist["Year"] == hist_year][target_metric_raw].values[0]
            calculated_target = base_hist * (1 + growth_pct / 100)
            if target_metric_raw == "cr":
                st.success(f"Target: **{calculated_target:.2%}** {metric_map[target_metric_raw]}")
            elif target_metric_raw == "aov":
                st.success(f"Target: **€{calculated_target:,.2f}** {metric_map[target_metric_raw]}")
            else:
                st.success(f"Target: **{calculated_target:,.0f}** {metric_map[target_metric_raw]}")
            st.markdown("---")

        col_d1, col_d2 = st.columns(2)
        st.session_state.tgt_start = col_d1.date_input(
            "Target Period Start", st.session_state.tgt_start)
        st.session_state.tgt_end   = col_d2.date_input(
            "Target Period End",   st.session_state.tgt_end)

        col_m1, col_m2, col_m3 = st.columns(3)
        m_opts = ["Revenue", "Conversions", "Sessions", "CR", "AOV"]
        default_idx = (
            m_opts.index(metric_map[target_metric_raw])
            if len(sel_brands) == 1 and metric_map[target_metric_raw] in m_opts
            else m_opts.index(st.session_state.target_metric)
            if st.session_state.target_metric in m_opts else 0
        )
        st.session_state.target_metric = col_m1.selectbox(
            "Final Target Metric", m_opts, index=default_idx)

        volume_driver = "Traffic (Sessions)"
        if st.session_state.target_metric in ["Revenue", "Conversions"]:
            d_opts = (
                ["Traffic (Sessions)", "Conversion Rate (CR)", "Avg. Order Value (AOV)"]
                if st.session_state.target_metric == "Revenue"
                else ["Traffic (Sessions)", "Conversion Rate (CR)"]
            )
            volume_driver = col_m2.selectbox("Scale via:", d_opts)

        if st.session_state.target_metric == "CR":
            st.session_state.target_val = col_m3.number_input(
                "Desired CR",
                value=float(calculated_target if len(sel_brands) == 1 else st.session_state.target_val),
                step=0.0001, format="%.4f",
            )
        elif st.session_state.target_metric == "AOV":
            st.session_state.target_val = col_m3.number_input(
                "Desired AOV (€)",
                value=float(calculated_target if len(sel_brands) == 1 else st.session_state.target_val),
                step=1.0,
            )
        else:
            st.session_state.target_val = col_m3.number_input(
                f"Desired {st.session_state.target_metric}",
                value=float(calculated_target if len(sel_brands) == 1 else st.session_state.target_val),
                step=1000.0,
            )

        df_tgt = df[
            (df["Date"].dt.date >= st.session_state.tgt_start) &
            (df["Date"].dt.date <= st.session_state.tgt_end)
        ].copy()

        if df_tgt.empty:
            st.warning("Target period has no data in the projection year. Adjust the dates above.")
            return

        tgt_rev_base  = df_tgt["Revenue_Base"].sum()
        tgt_conv_base = df_tgt["Conversions_Base"].sum()
        tgt_sess_base = df_tgt["Sessions_Base"].sum()
        tgt_eff_aov   = tgt_rev_base  / tgt_conv_base if tgt_conv_base > 0 else base_aov
        tgt_eff_cr    = tgt_conv_base / tgt_sess_base if tgt_sess_base > 0 else base_cr

        needed_rev = needed_conv = needed_sess = 0.0
        tm, tv = st.session_state.target_metric, st.session_state.target_val

        if tm == "Revenue":
            if volume_driver == "Traffic (Sessions)":
                needed_rev  = tv
                needed_conv = needed_rev  / tgt_eff_aov if tgt_eff_aov > 0 else 0
                needed_sess = needed_conv / tgt_eff_cr  if tgt_eff_cr  > 0 else 0
            elif volume_driver == "Conversion Rate (CR)":
                needed_sess = tgt_sess_base; needed_rev = tv
                needed_conv = needed_rev / tgt_eff_aov if tgt_eff_aov > 0 else 0
            else:
                needed_sess = tgt_sess_base; needed_conv = tgt_conv_base; needed_rev = tv
        elif tm == "Conversions":
            if volume_driver == "Traffic (Sessions)":
                needed_conv = tv
                needed_sess = needed_conv / tgt_eff_cr  if tgt_eff_cr  > 0 else 0
                needed_rev  = needed_conv * tgt_eff_aov
            else:
                needed_sess = tgt_sess_base; needed_conv = tv; needed_rev = tv * tgt_eff_aov
        elif tm == "Sessions":
            needed_sess = tv; needed_conv = tv * tgt_eff_cr; needed_rev = needed_conv * tgt_eff_aov
        elif tm == "CR":
            needed_sess = tgt_sess_base; needed_conv = tgt_sess_base * tv
            needed_rev  = needed_conv * tgt_eff_aov
        else:  # AOV
            needed_conv = tgt_conv_base; needed_sess = tgt_sess_base
            needed_rev  = needed_conv * tv

        needed_cr  = needed_conv / needed_sess if needed_sess > 0 else 0
        needed_aov = needed_rev  / needed_conv if needed_conv > 0 else 0

        s_s   = df_tgt["Sessions_Sim"].sum()
        s_c   = df_tgt["Conversions_Sim"].sum()
        s_r   = df_tgt["Revenue_Sim"].sum()
        s_cr  = s_c / s_s if s_s > 0 else 0
        s_aov = s_r / s_c if s_c > 0 else 0

        kpi_cols = st.columns(5)
        labels = ["Sessions", "Conversions", "Revenue", "CR", "AOV"]
        needed = [needed_sess, needed_conv, needed_rev, needed_cr, needed_aov]
        before = [tgt_sess_base, tgt_conv_base, tgt_rev_base, tgt_eff_cr, tgt_eff_aov]
        after  = [s_s, s_c, s_r, s_cr, s_aov]

        for col, lbl, n_v, b_v, a_v in zip(kpi_cols, labels, needed, before, after):
            col.metric(f"Needed {lbl}", _fmt(lbl, n_v))
            col.caption(f"**Before:** {_fmt(lbl, b_v)}")
            if has_events:
                delta = a_v - b_v
                sign  = "+" if delta >= 0 else ""
                col.caption(f"**After:** {_fmt(lbl, a_v)} *(Δ {sign}{_fmt(lbl, delta)})*")

        agg_tgt = df_tgt.groupby(time_col).agg({
            "Date": "first",
            "Sessions_Sim": "sum", "Conversions_Sim": "sum", "Revenue_Sim": "sum",
            "Sessions_Base": "sum", "Conversions_Base": "sum", "Revenue_Base": "sum",
        }).reset_index()

        for col_n, total in [("Needed_Revenue", needed_rev),
                              ("Needed_Conversions", needed_conv),
                              ("Needed_Sessions",   needed_sess)]:
            base_c = col_n.replace("Needed_", "") + "_Base"
            bt = agg_tgt[base_c].sum()
            agg_tgt[col_n] = total * (agg_tgt[base_c] / bt) if bt > 0 else 0

        for sfx in ["Base", "Sim"]:
            agg_tgt[f"Gap_Revenue_{sfx}"]     = agg_tgt[f"Revenue_{sfx}"]     - agg_tgt["Needed_Revenue"]
            agg_tgt[f"Gap_Conversions_{sfx}"] = agg_tgt[f"Conversions_{sfx}"] - agg_tgt["Needed_Conversions"]
            agg_tgt[f"Gap_Sessions_{sfx}"]    = agg_tgt[f"Sessions_{sfx}"]    - agg_tgt["Needed_Sessions"]

        st.markdown("---")
        gap_m = st.radio("Visualize Tracking For:", ["Revenue", "Conversions", "Sessions"], horizontal=True)

        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=agg_tgt["Date"], y=agg_tgt[f"Needed_{gap_m}"],
            mode="lines", line=dict(color=_C_TARGET, dash="dash", width=2), name="Target"))
        fig_ts.add_trace(go.Scatter(
            x=agg_tgt["Date"], y=agg_tgt[f"{gap_m}_Base"],
            mode="lines", line=dict(color=_C_BASE, dash="dot", width=2), name="Before"))
        if has_events:
            fig_ts.add_trace(go.Scatter(
                x=agg_tgt["Date"], y=agg_tgt[f"{gap_m}_Sim"],
                mode="lines+markers", line=dict(color=_C_SIM, width=2), name="After"))
            _add_shock_markers(fig_ts, event_log)
        fig_ts.update_layout(
            template=_TEMPLATE, height=350,
            title=dict(text=f"Target vs Forecast — {gap_m}", font=dict(color="#12124a")),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_ts, use_container_width=True)

        fig_gap = go.Figure()
        fig_gap.add_trace(go.Bar(
            x=agg_tgt["Date"], y=agg_tgt[f"Gap_{gap_m}_Base"],
            name="Gap (Before)", marker_color="#cbd5e1"))
        if has_events:
            colors = ["#f87171" if v < 0 else "#4ade80" for v in agg_tgt[f"Gap_{gap_m}_Sim"]]
            fig_gap.add_trace(go.Bar(
                x=agg_tgt["Date"], y=agg_tgt[f"Gap_{gap_m}_Sim"],
                name="Gap (After)", marker_color=colors))
        fig_gap.update_layout(
            template=_TEMPLATE, barmode="group", height=280,
            title=dict(text=f"{gap_m} Surplus / Shortfall", font=dict(color="#12124a")),
        )
        st.plotly_chart(fig_gap, use_container_width=True)

        if has_events:
            disp_cols = [
                "Date",
                "Needed_Revenue",      "Revenue_Base",      "Revenue_Sim",      "Gap_Revenue_Base",      "Gap_Revenue_Sim",
                "Needed_Conversions",  "Conversions_Base",  "Conversions_Sim",  "Gap_Conversions_Base",  "Gap_Conversions_Sim",
                "Needed_Sessions",     "Sessions_Base",     "Sessions_Sim",     "Gap_Sessions_Base",     "Gap_Sessions_Sim",
            ]
            gap_cols = [
                "Gap_Revenue_Base",      "Gap_Revenue_Sim",
                "Gap_Conversions_Base",  "Gap_Conversions_Sim",
                "Gap_Sessions_Base",     "Gap_Sessions_Sim",
            ]
        else:
            disp_cols = [
                "Date",
                "Needed_Revenue",     "Revenue_Base",     "Gap_Revenue_Base",
                "Needed_Conversions", "Conversions_Base", "Gap_Conversions_Base",
                "Needed_Sessions",    "Sessions_Base",    "Gap_Sessions_Base",
            ]
            gap_cols = ["Gap_Revenue_Base", "Gap_Conversions_Base", "Gap_Sessions_Base"]

        disp_df = agg_tgt[disp_cols].copy()
        try:
            st.dataframe(disp_df.style.map(color_neg, subset=gap_cols), use_container_width=True)
        except AttributeError:
            st.dataframe(disp_df.style.applymap(color_neg, subset=gap_cols), use_container_width=True)
