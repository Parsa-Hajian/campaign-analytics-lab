import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH  = os.path.join(ASSETS_DIR, "logo.png")

PROFILES_PATH   = os.path.join(DATA_DIR, "brand_profiles.csv")
YEARLY_KPI_PATH = os.path.join(DATA_DIR, "yearly_kpis.csv")
DATASET_PATH    = os.path.join(DATA_DIR, "transactions.csv")
LOG_PATH        = os.path.join(DATA_DIR, "activity_log.csv")
SETTINGS_PATH   = os.path.join(DATA_DIR, "settings.json")

# Campaign event shapes: display name → internal distribution type
EVENT_MAPPING = {
    "Email Campaign":  "Front-Loaded",
    "Flash Sale":      "Linear Fade",
    "Product Launch":  "Delayed Peak",
    "Awareness Drive": "Step",
}
