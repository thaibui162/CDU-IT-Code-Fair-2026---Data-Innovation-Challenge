"""
load_data.py
Step 1 - Load and clean the two source files.

Mirrors the Power Query queries:
  * Communities_Base  -> load_communities()
  * HealthFacilities  -> load_health_facilities()

Run on its own to preview the cleaned tables:
    python load_data.py
"""
import numpy as np
import pandas as pd

import config


def load_communities(path=config.COMMUNITIES_CSV) -> pd.DataFrame:
    """Load communities.csv (File B) and apply the Communities_Base steps."""
    # Read everything as text first, like Csv.Document, then set types explicitly.
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")

    # Remove blank / summary rows (Community empty)
    df = df[df["Community"].str.strip() != ""].copy()

    # Short column names
    df = df.rename(columns=config.RENAME_COMMUNITIES)

    # Data types (decimal point is always "." -> equivalent to culture en-US)
    df["Community_ID"] = pd.to_numeric(df["Community_ID"]).astype("Int64")
    df["Population"] = pd.to_numeric(df["Population"].replace("", np.nan)).astype("Int64")
    for c in ["Latitude", "Longitude"] + config.SERVICE_COLS:
        df[c] = pd.to_numeric(df[c].replace("", np.nan)).astype(float)

    # Clean text
    df["Community"] = df["Community"].str.strip()
    df["Community_Type"] = df["Community_Type"].str.strip()
    df["NTG_Region"] = df["NTG_Region"].str.strip().str.title()

    # Population = 0 means missing: flag it, then blank it
    df["Population_Missing"] = df["Population"].isna() | (df["Population"] == 0)
    df.loc[df["Population"] == 0, "Population"] = pd.NA

    # Island / Mainland
    df["Location_Type"] = np.where(df["Community"].isin(config.ISLAND_LIST), "Island", "Mainland")

    return df.reset_index(drop=True)


def load_health_facilities(path=config.HEALTH_CSV) -> pd.DataFrame:
    """Load Health_Services_clean.csv and apply the HealthFacilities steps."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")

    # Blank text -> null
    df = df.replace("", np.nan)

    df["Latitude"] = pd.to_numeric(df["Latitude"]).astype(float)
    df["Longitude"] = pd.to_numeric(df["Longitude"]).astype(float)

    df = df.rename(columns={"Opening hours": "Opening_Hours"})
    df = df.drop(columns=[c for c in ["Mail address", "Fax"] if c in df.columns])

    df["Has_Coordinates"] = df["Latitude"].notna() & df["Longitude"].notna()
    return df.reset_index(drop=True)


if __name__ == "__main__":
    com = load_communities()
    hf = load_health_facilities()
    print(f"Communities_Base : {len(com)} rows, {com.shape[1]} columns")
    print(f"HealthFacilities : {len(hf)} rows, {int(hf['Has_Coordinates'].sum())} with coordinates")
    print(com.head(3).to_string())
