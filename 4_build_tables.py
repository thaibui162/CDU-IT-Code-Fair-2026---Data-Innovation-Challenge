"""
build_tables.py
Step 3 - Supporting tables used by the dashboard.

Mirrors the Power Query queries:
  * ServiceStatus  - long table, 1 row = community x service (1,950 rows)
  * MapStatus      - long table for map colouring (1,950 rows)
  * DimService     - service list with group and sort order
  * DimStatus      - 3 statuses with colour

Run on its own to preview:
    python build_tables.py
"""
import pandas as pd

import config


def status_label(v) -> str:
    if v == 1:
        return "Available"
    if v == 0:
        return "Not available"
    return "Unverified"


def build_service_status(communities: pd.DataFrame) -> pd.DataFrame:
    long = communities.melt(id_vars=["Community_ID"], value_vars=config.SERVICE_COLS,
                            var_name="Service_Key", value_name="Value")
    long["Status"] = long["Value"].map(status_label)
    # same row order as Table.UnpivotOtherColumns (community by community)
    order = {k: i for i, k in enumerate(config.SERVICE_COLS)}
    long["_o"] = long["Service_Key"].map(order)
    long["_r"] = long.groupby("Service_Key").cumcount()
    return long.sort_values(["_r", "_o"]).drop(columns=["_o", "_r"]).reset_index(drop=True)


def build_map_status(communities: pd.DataFrame) -> pd.DataFrame:
    spec = [
        ("Connectivity", "Overall", 0, "Connectivity_Level"),
        ("Connectivity", "Internet", 1, "Internet"),
        ("Connectivity", "Mobile phone", 2, "Mobile"),
        ("Connectivity", "WiFi", 3, "WiFi"),
        ("Services", "Overall", 0, "Services_Level"),
        ("Services", "Health centre", 1, "Health"),
        ("Services", "Police station", 2, "Police"),
        ("Services", "Community store", 3, "Store"),
        ("Services", "School", 4, "School"),
        ("Services", "Council service centre", 5, "Council"),
    ]
    rows = []
    for _, r in communities.iterrows():
        for m, f, o, col in spec:
            status = r[col] if f == "Overall" else status_label(r[col])
            rows.append((r["Community_ID"], m, f, o, status))
    df = pd.DataFrame(rows, columns=["Community_ID", "Map", "Factor", "Factor_Order", "Status"])
    df["Status_Label"] = df["Status"].replace({"Full": "All available", "Partial": "Some available", "None": "None available"})
    order = {"All available": 1, "Available": 1, "Some available": 2, "None available": 3, "Not available": 3}
    df["Status_Order"] = df["Status_Label"].map(order).fillna(4).astype(int)
    return df


def build_dim_service() -> pd.DataFrame:
    return pd.DataFrame([
        ("Internet", "Internet", "Connectivity", False, 1, 1),
        ("Mobile", "Mobile phone", "Connectivity", True, 1, 2),
        ("WiFi", "WiFi", "Connectivity", False, 1, 3),
        ("Health", "Health centre", "Services", True, 2, 4),
        ("Police", "Police station", "Services", True, 2, 5),
        ("Store", "Community store", "Services", True, 2, 6),
        ("School", "School", "Services", False, 2, 7),
        ("Council", "Council service centre", "Services", False, 2, 8),
        ("Road", "Road access", "Access", False, 3, 9),
        ("Aerodrome", "Aerodrome", "Access", False, 3, 10),
    ], columns=["Service_Key", "Service_Name", "Service_Group", "Is_Critical", "Group_Order", "Service_Order"])


def build_dim_status() -> pd.DataFrame:
    return pd.DataFrame([
        ("Not available", 1, "#E07A5F"),
        ("Unverified", 2, "#C9C3E6"),
        ("Available", 3, "#81B29A"),
    ], columns=["Status", "Status_Order", "Status_Color"])


if __name__ == "__main__":
    from process_communities import build_communities
    com = build_communities()
    print("ServiceStatus:", len(build_service_status(com)), "rows")
    print("MapStatus    :", len(build_map_status(com)), "rows")
    print("DimService   :", len(build_dim_service()), "rows")
    print("DimStatus    :", len(build_dim_status()), "rows")
