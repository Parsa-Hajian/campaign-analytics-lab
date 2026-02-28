# Campaign Analytics Lab

A decision-intelligence platform for marketing and commercial teams.

**What it does:** combines historical demand modeling with forward-looking scenario simulation to answer *"What should my business do organically — and what will my campaigns contribute?"*

---

## Features

| Module | Description |
|--------|-------------|
| 📈 Projection Overview | Full-year baseline + simulation forecast with ±15% confidence bands |
| 🎯 Goal Tracker | Target translation — what Sessions/Conversions/Revenue do I need? |
| 🧬 DNA Profile | Visualize your seasonal demand shape (Sessions, CR, AOV) |
| 🚀 Campaign Simulation | Inject time-bound events with 4 shape profiles |
| 🖱️ DNA Drag | Sculpt individual period indices interactively |
| 🔄 DNA Swap | Swap demand patterns between two time periods |
| 🧹 De-Shock Tool | Isolate artificial demand from historical events; build a signature library |
| 📋 Audit & Attribution | Marginal contribution of each event to the target metric |
| 📊 Excel Export | Download full projection report |

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/Parsa-Hajian/campaign-analytics-lab.git
cd campaign-analytics-lab
pip install -r requirements.txt

# 2. Generate demo data (already included — only needed if you regenerate)
python generate_data.py

# 3. Launch
streamlit run app.py
```

**Demo credentials:** `demo` / `demo2026`

---

## Using Your Own Data

1. Replace `data/transactions.csv` with your own data (same schema — see Documentation tab)
2. Run `python generate_data.py` to regenerate `brand_profiles.csv` and `yearly_kpis.csv`
3. Restart the app

```
transactions.csv columns:
  Date, brand, sessions, conversions, revenue, cr, aov, campaign, campaign_volume
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_USERNAME` | `demo` | Login username |
| `APP_PASSWORD` | `demo2026` | Login password |
| `APP_EMAIL` | *(default)* | Contact email shown in sidebar |

---

## Deploy to Streamlit Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account → select this repo → main file: `app.py`
4. Set environment variables in the Streamlit Cloud secrets panel

---

## Architecture

```
transactions.csv  →  brand_profiles.csv  →  DNA (35% overall + 65% weighted history)
                                         →  Calibration (base_sessions, base_CR, base_AOV)
                                         →  Projections (Baseline + Simulation ± 15%)
```

See the **📖 Documentation** tab inside the app for full formula derivations, model assumptions, and a step-by-step usage guide.

---

## License

MIT — free to use, modify, and distribute.
