# Data_Processing

These Python scripts rebuild the Power BI data model for the IT Code Fair 2026 – Data Innovation dashboard, using the same logic as the Power Query steps.

## Requirements
- Python 3.9 or newer, with `pandas` and `numpy` (`pip install pandas numpy`).
- `communities.csv` and `Health_Services_clean.csv` must be in the folder above this one (`Data Innovation 2026`).

## Run
```bash
cd Data_Processing
python export_final.py          # creates output/communities_final.csv
python export_final.py --all    # also exports the supporting tables
```
Before saving, the script checks 27 values (row counts, levels, distances and more) against the Power BI results and prints OK or MISMATCH for each one.

## Files
| File | Role | Matching Power Query step |
|---|---|---|
| `config.py` | Paths, column names, weights, island list, 50 km threshold | – |
| `load_data.py` | Loads and cleans the two CSV files | Communities_Base, HealthFacilities |
| `process_communities.py` | Distance to the nearest health centre, group levels, access, flags, notes, vulnerable score and level | HealthDestinations, Communities |
| `build_tables.py` | Long tables and dimension tables | ServiceStatus, MapStatus, DimService, DimStatus |
| `validate.py` | Compares the results with the Power BI numbers | – |
| `export_final.py` | Runs the whole pipeline and writes the CSV files | – |

## Vulnerable score columns in `communities_final.csv`
- `Service_Score` = 2 × (Health + Police + Store + Mobile) + (School + Council + Internet + WiFi). The maximum is 12.
- `Service_Gap` (vulnerable gap score) = (12 − Service_Score) / 12 × 100. 0 means all services are present and 100 means none are.
- `Critical_Missing` = the number of the 4 critical services with a value below 1 (0.5 counts as missing).
- `Vulnerability_Level`:
  - **Critical**: 3 or more critical services missing, no aerodrome, and the nearest health centre more than 50 km away.
  - **High**: 3 or more critical services missing, or 2 missing with no aerodrome.
  - **Medium**: 1–2 critical services missing.
  - **Low**: all 4 critical services present.

Rows are sorted by level, then by population from largest to smallest.
