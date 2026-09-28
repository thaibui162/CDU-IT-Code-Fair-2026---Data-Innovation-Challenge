"""
process_communities.py
Step 2 - Build the main Communities table.

Mirrors the Power Query queries HealthDestinations and Communities:
  A. Distance to the nearest health centre (straight line, Haversine)
  B. Connectivity_Level / Services_Level
  C. Access_Mode
  D. Digital divide flags
  E. Notes for the tooltip (unverified items)
  F. Vulnerable score: Service_Score, Service_Gap, Critical_Missing,
     Vulnerability_Level, Level_Order, Level_Caveat
  G. Community_Label and sort-order columns

Run on its own to preview:
    python process_communities.py
"""
import numpy as np
import pandas as pd

import config
from load_data import load_communities, load_health_facilities


# ------------------------------------------------------------------------------
# A. Distance to nearest health centre
# ------------------------------------------------------------------------------
def build_health_destinations(communities: pd.DataFrame, facilities: pd.DataFrame) -> pd.DataFrame:
    """80 facilities with coordinates + communities with Health = 1 (same order as PBI)."""
    fac = facilities[facilities["Has_Coordinates"]][["Location", "Latitude", "Longitude", "Phone"]]
    fac = fac.rename(columns={"Location": "Dest_Name"})
    com = communities[communities["Health"] == 1][["Community", "Latitude", "Longitude"]]
    com = com.rename(columns={"Community": "Dest_Name"}).assign(Phone=np.nan)
    return pd.concat([fac, com], ignore_index=True)


def haversine_km(lat1, lon1, lat2, lon2):
    r = np.pi / 180
    dlat = (lat2 - lat1) * r
    dlon = (lon2 - lon1) * r
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1 * r) * np.cos(lat2 * r) * np.sin(dlon / 2) ** 2
    return 2 * config.EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def add_nearest_health(df: pd.DataFrame, dest: pd.DataFrame) -> pd.DataFrame:
    d_lat, d_lon = dest["Latitude"].to_numpy(), dest["Longitude"].to_numpy()
    dist, name, phone = [], [], []
    for _, row in df.iterrows():
        if row["Health"] == 1:
            dist.append(0.0); name.append("On site"); phone.append(None)
            continue
        d = haversine_km(row["Latitude"], row["Longitude"], d_lat, d_lon)
        j = int(np.argmin(d))                      # first minimum, like Table.Min
        dist.append(round(float(d[j]), 1))         # banker's rounding, like Number.Round
        name.append(dest["Dest_Name"].iat[j])
        p = dest["Phone"].iat[j]
        phone.append(p if isinstance(p, str) else None)
    df["Dist_Health_km"] = dist
    df["Nearest_Health"] = name
    df["Nearest_Health_Phone"] = phone
    return df


# ------------------------------------------------------------------------------
# B-G. Row-level calculations
# ------------------------------------------------------------------------------
def group_level(values) -> str:
    """Full = all 1 | Partial = at least one 1 | None = all 0 | Unverified = otherwise."""
    n = len(values)
    ones = sum(v == 1 for v in values)
    zeros = sum(v == 0 for v in values)
    if ones == n:
        return "Full"
    if ones > 0:
        return "Partial"
    if zeros == n:
        return "None"
    return "Unverified"


def access_mode(road, aero) -> str:
    if road == 1 and aero == 1:
        return "Road + Air"
    if road == 1 and aero == 0:
        return "Road only"
    if road == 0 and aero == 1:
        return "Air only"
    if road == 0 and aero == 0:
        return "No road or airstrip"
    return "Unverified"


def vulnerability_level(critical_missing, aerodrome, dist_km) -> str:
    no_air = aerodrome < 1
    far = dist_km > config.FAR_FROM_HEALTH_KM
    if critical_missing >= 3 and no_air and far:
        return "Critical"
    if critical_missing >= 3 or (critical_missing == 2 and no_air):
        return "High"
    if critical_missing >= 1:
        return "Medium"
    return "Low"


LEVEL_ORDER = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
GROUP_ORDER = {"Full": 1, "Partial": 2, "None": 3}   # anything else -> 4


def build_communities(communities: pd.DataFrame = None, facilities: pd.DataFrame = None) -> pd.DataFrame:
    if communities is None:
        communities = load_communities()
    if facilities is None:
        facilities = load_health_facilities()
    df = communities.copy()

    # A. Nearest health centre
    dest = build_health_destinations(df, facilities)
    df = add_nearest_health(df, dest)

    # B. Group levels
    df["Connectivity_Level"] = df[config.CONNECTIVITY_COLS].apply(lambda r: group_level(list(r)), axis=1)
    df["Services_Level"] = df[config.SERVICES_COLS].apply(lambda r: group_level(list(r)), axis=1)

    # C. Access
    df["Access_Mode"] = [access_mode(r, a) for r, a in zip(df["Road"], df["Aerodrome"])]

    # D. Digital divide flags
    df["School_No_Internet"] = (df["School"] == 1) & (df["Internet"] != 1)
    df["Health_No_Internet"] = (df["Health"] == 1) & (df["Internet"] != 1)

    # E. Notes
    def unverified_note(row):
        names = [config.SERVICE_LABELS[c] for c in config.SERVICE_COLS if row[c] == 0.5]
        return "Unverified: " + ", ".join(names) if names else None

    def critical_to_verify(row):
        names = [config.SERVICE_LABELS[c] for c in config.CRITICAL_COLS if row[c] == 0.5]
        return ", ".join(names) if names else None

    df["Unverified_Note"] = df.apply(unverified_note, axis=1)
    df["Critical_To_Verify"] = df.apply(critical_to_verify, axis=1)
    df["Critical_To_Verify_Count"] = (df[config.CRITICAL_COLS] == 0.5).sum(axis=1).astype(int)

    # F. Vulnerable score
    df["Service_Score"] = 2 * df[config.CRITICAL_COLS].sum(axis=1) + df[config.OTHER_SCORED_COLS].sum(axis=1)
    df["Service_Gap"] = [round((config.MAX_SCORE - s) / config.MAX_SCORE * 100) for s in df["Service_Score"]]
    df["Critical_Missing"] = (df[config.CRITICAL_COLS] < 1).sum(axis=1).astype(int)   # 0.5 counts as missing
    df["Vulnerability_Level"] = [vulnerability_level(m, a, d) for m, a, d in
                                 zip(df["Critical_Missing"], df["Aerodrome"], df["Dist_Health_km"])]
    df["Level_Order"] = df["Vulnerability_Level"].map(LEVEL_ORDER)
    df["Level_Caveat"] = [
        f"Counts unverified {v} as missing; level may be lower once verified" if n > 0 else None
        for v, n in zip(df["Critical_To_Verify"], df["Critical_To_Verify_Count"])
    ]

    # G. Display label ("Five Mile" appears twice) and sort-order columns
    dup = df["Community"].duplicated(keep=False)
    df["Community_Label"] = np.where(dup, df["Community"] + " (" + df["Community_ID"].astype(str) + ")", df["Community"])
    df["Conn_Level_Order"] = df["Connectivity_Level"].map(GROUP_ORDER).fillna(4).astype(int)
    df["Svc_Level_Order"] = df["Services_Level"].map(GROUP_ORDER).fillna(4).astype(int)

    return df


if __name__ == "__main__":
    out = build_communities()
    print(f"Communities: {len(out)} rows, {out.shape[1]} columns")
    print(out["Vulnerability_Level"].value_counts().to_string())
