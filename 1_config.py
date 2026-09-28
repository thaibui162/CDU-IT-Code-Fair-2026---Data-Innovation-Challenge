"""
config.py
Shared settings for the Data_Processing pipeline.

Folder layout this pipeline expects:

    Data Innovation 2026/
    ├── communities.csv               <- File B (BushTel), raw source, never edited
    ├── Health_Services_clean.csv     <- NT Health facilities (hand-cleaned copy)
    └── Data_Processing/
        ├── config.py                 <- this file
        ├── load_data.py
        ├── process_communities.py
        ├── build_tables.py
        ├── validate.py
        ├── export_final.py
        └── output/                   <- created automatically

All logic mirrors the Power Query steps in the Power BI file, so the Python
output matches the PBI model row for row.
"""
from pathlib import Path

# --- Paths --------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent                      # folder that holds the CSV files
OUTPUT_DIR = SCRIPT_DIR / "output"

COMMUNITIES_CSV = DATA_DIR / "communities.csv"
HEALTH_CSV = DATA_DIR / "Health_Services_clean.csv"

# --- Column renames (same as Power Query "Renamed" step) -----------------------
RENAME_COMMUNITIES = {
    "Health centre": "Health",
    "Police station": "Police",
    "Regional council service centre": "Council",
    "Community store": "Store",
    "Mobile phone": "Mobile",
    "Accessible by road": "Road",
}

SERVICE_COLS = ["Health", "Police", "School", "Council", "Store",
                "Internet", "Mobile", "WiFi", "Road", "Aerodrome"]
CONNECTIVITY_COLS = ["Internet", "Mobile", "WiFi"]
SERVICES_COLS = ["Health", "Police", "School", "Council", "Store"]

# Vulnerable score: critical services weigh x2, other services x1.
# Road and Aerodrome are not scored (Aerodrome is used only for the level).
CRITICAL_COLS = ["Health", "Police", "Store", "Mobile"]
OTHER_SCORED_COLS = ["School", "Council", "Internet", "WiFi"]
MAX_SCORE = 12

# Level rule threshold (km, straight line)
FAR_FROM_HEALTH_KM = 50

EARTH_RADIUS_KM = 6371

# 24 island communities, inferred from coordinates (team to confirm)
ISLAND_LIST = [
    "Angurugu", "Galiwinku", "Milikapiti", "Milingimbi", "Milyakburra", "Minjilang",
    "Pickertaramoor", "Pirlangimpi", "Umbakumba", "Warruwi", "Wurankuwu", "Wurrumiyanga",
    "Alamirra", "Bardalumba", "Bodia", "Dhambala", "Dhudupu", "Galawarra", "Gutjangan",
    "Malkala", "Ngadumiyerrka", "Ngayawilli", "Paru", "Sandy Bay",
]

# Display labels used in notes and in the long tables
SERVICE_LABELS = {
    "Health": "Health centre", "Police": "Police station", "School": "School",
    "Council": "Council", "Store": "Community store", "Internet": "Internet",
    "Mobile": "Mobile phone", "WiFi": "WiFi", "Road": "Road", "Aerodrome": "Aerodrome",
}
