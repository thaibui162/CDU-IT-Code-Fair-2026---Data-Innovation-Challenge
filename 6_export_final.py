"""
export_final.py
Step 5 - Run the whole pipeline and export the final table to CSV.

Usage (from inside the Data_Processing folder):
    python export_final.py            -> output/communities_final.csv
    python export_final.py --all      -> also exports ServiceStatus, MapStatus,
                                         DimService, DimStatus, HealthFacilities

The final CSV has one row per community (195 rows) and includes the
vulnerable score columns:
    Service_Score        0-12, higher = more services
    Service_Gap          vulnerable gap score, 0-100 (0 = all services, 100 = none)
    Critical_Missing     number of the 4 critical services missing (0.5 counts as missing)
    Vulnerability_Level  Critical / High / Medium / Low
"""
import argparse
import sys

import config
from load_data import load_communities, load_health_facilities
from process_communities import build_communities
from build_tables import build_service_status, build_map_status, build_dim_service, build_dim_status
from validate import validate

FINAL_COLUMNS = [
    # Identity
    "Community_ID", "Community", "Community_Label", "Community_Type", "NTG_Region", "Location_Type",
    "Population", "Population_Missing", "Latitude", "Longitude",
    # Raw service values (1 = yes, 0 = no, 0.5 = unverified)
    "Health", "Police", "Store", "Mobile", "School", "Council", "Internet", "WiFi", "Road", "Aerodrome",
    # Group status
    "Connectivity_Level", "Services_Level", "Access_Mode",
    "School_No_Internet", "Health_No_Internet",
    # Nearest health centre
    "Dist_Health_km", "Nearest_Health", "Nearest_Health_Phone",
    # Vulnerable score
    "Service_Score", "Service_Gap", "Critical_Missing", "Vulnerability_Level", "Level_Order",
    # Data notes
    "Critical_To_Verify", "Critical_To_Verify_Count", "Level_Caveat", "Unverified_Note",
]


def main():
    parser = argparse.ArgumentParser(description="Build the final communities table.")
    parser.add_argument("--all", action="store_true", help="also export the supporting tables")
    args = parser.parse_args()

    print(f"Reading  {config.COMMUNITIES_CSV.name} and {config.HEALTH_CSV.name} from {config.DATA_DIR}")
    base = load_communities()
    facilities = load_health_facilities()
    com = build_communities(base, facilities)
    service_status = build_service_status(com)
    map_status = build_map_status(com)

    print("Validating against Power BI results:")
    passed = validate(com, service_status, map_status)

    config.OUTPUT_DIR.mkdir(exist_ok=True)
    final = com[FINAL_COLUMNS].sort_values(["Level_Order", "Population", "Dist_Health_km"],
                                           ascending=[True, False, False], na_position="last")
    out = config.OUTPUT_DIR / "communities_final.csv"
    final.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved {out}  ({len(final)} rows, {final.shape[1]} columns)")

    if args.all:
        tables = {
            "service_status.csv": service_status,
            "map_status.csv": map_status,
            "dim_service.csv": build_dim_service(),
            "dim_status.csv": build_dim_status(),
            "health_facilities.csv": facilities,
        }
        for name, t in tables.items():
            t.to_csv(config.OUTPUT_DIR / name, index=False, encoding="utf-8-sig")
            print(f"Saved {config.OUTPUT_DIR / name}  ({len(t)} rows)")

    if not passed:
        print("\nWARNING: some checks differ from the Power BI results (see MISMATCH lines above).")
        sys.exit(1)
    print("\nDone - all checks match Power BI.")


if __name__ == "__main__":
    main()
