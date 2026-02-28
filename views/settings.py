"""Settings page — campaign default coefficients per entity."""
import os
import pandas as pd
import streamlit as st

try:
    from config import EVENT_MAPPING, PROFILES_PATH
except ImportError:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROFILES_PATH = os.path.join(_ROOT, "data", "brand_profiles.csv")
    EVENT_MAPPING = {
        "Email Campaign": "Front-Loaded", "Flash Sale": "Linear Fade",
        "Product Launch": "Delayed Peak", "Awareness Drive": "Step",
    }

from engine.settings_store import load_settings, save_settings

_SHAPES = list(EVENT_MAPPING.keys())


def render_settings():
    settings = load_settings()

    st.markdown("### Campaign Default Coefficients")
    st.caption(
        "Set the default Traffic Lift (%) for each campaign shape per entity. "
        "These values pre-populate the slider in the Simulation Lab when you select a shape.")

    try:
        profiles   = pd.read_csv(PROFILES_PATH)
        all_brands = sorted(profiles["brand"].str.strip().str.lower().unique())
    except Exception:
        all_brands = []

    cd = settings.get("campaign_defaults", {"__all__": {s: 25 for s in _SHAPES}})

    rows = []
    for b in ["__all__"] + all_brands:
        label = "Global Default" if b == "__all__" else b.title()
        row   = {"Entity": label}
        for shape in _SHAPES:
            row[shape] = int(cd.get(b, cd.get("__all__", {})).get(shape, 25))
        rows.append(row)

    df_defaults = pd.DataFrame(rows)

    col_cfg = {"Entity": st.column_config.TextColumn("Entity", disabled=True)}
    for shape in _SHAPES:
        col_cfg[shape] = st.column_config.NumberColumn(
            shape, min_value=-100, max_value=300, step=5, format="%d %%",
            help=f"Default traffic lift (%) for {shape} campaigns",
        )

    edited = st.data_editor(
        df_defaults, column_config=col_cfg,
        use_container_width=True, hide_index=True, key="campaign_defaults_editor",
    )

    st.markdown("---")
    col_apply, col_save, _ = st.columns([1.5, 1.5, 3])

    with col_apply:
        if st.button("Apply Global to All Entities", use_container_width=True):
            global_row = edited[edited["Entity"] == "Global Default"]
            if not global_row.empty:
                global_vals = {s: int(global_row.iloc[0][s]) for s in _SHAPES}
                new_cd = {"__all__": global_vals}
                for b in all_brands:
                    new_cd[b] = dict(global_vals)
                settings["campaign_defaults"] = new_cd
                save_settings(settings)
                st.success("Global defaults applied to all entities.")
                st.rerun()

    with col_save:
        if st.button("Save Settings", type="primary", use_container_width=True):
            new_cd = {}
            for _, row in edited.iterrows():
                label = row["Entity"]
                key   = "__all__" if label == "Global Default" else label.lower()
                new_cd[key] = {s: int(row[s]) for s in _SHAPES}
            settings["campaign_defaults"] = new_cd
            save_settings(settings)
            st.success("Settings saved.")
            st.rerun()

    with st.expander("Current effective defaults per entity"):
        preview_rows = []
        for b in all_brands:
            row = {"Entity": b.title()}
            for s in _SHAPES:
                val = int(cd.get(b, cd.get("__all__", {})).get(s, 25))
                row[s] = f"{val}%"
            preview_rows.append(row)
        if preview_rows:
            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No entities loaded yet.")
