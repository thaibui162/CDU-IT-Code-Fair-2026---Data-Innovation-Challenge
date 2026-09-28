"""
validate.py
Step 4 - Check that the Python results match the Power BI model.

The expected values below are the same checks used after building the PBI
model (communities.csv + Health_Services_clean.csv). If a source file changes,
update the expected values together with the team.

Run on its own:
    python validate.py
"""
import pandas as pd

EXPECTED = {
    "Communities rows": 195,
    "Total population": 40730,
    "Population missing": 28,
    "Island": 24,
    "Mainland": 171,
    "Connectivity None": 105,
    "Connectivity Full": 47,
    "Connectivity Partial": 43,
    "Services Full": 30,
    "Services Partial": 58,
    "Services None": 100,
    "Services Unverified": 7,
    "Access Road only": 116,
    "Access Road + Air": 52,
    "Access No road or airstrip": 18,
    "Access Air only": 9,
    "School_No_Internet": 21,
    "Health_No_Internet": 20,
    "Critical_To_Verify > 0": 15,
    "Mean Service_Score (x100)": 425,
    "Level Critical": 10,
    "Level High": 115,
    "Level Medium": 39,
    "Level Low": 31,
    "Manmoyi Dist_Health_km (x10)": 557,
    "ServiceStatus rows": 1950,
    "MapStatus rows": 1950,
}


def actual_values(com: pd.DataFrame, service_status=None, map_status=None) -> dict:
    vc = lambda col, v: int((com[col] == v).sum())
    a = {
        "Communities rows": len(com),
        "Total population": int(com["Population"].fillna(0).sum()),
        "Population missing": int(com["Population_Missing"].sum()),
        "Island": vc("Location_Type", "Island"),
        "Mainland": vc("Location_Type", "Mainland"),
        "Connectivity None": vc("Connectivity_Level", "None"),
        "Connectivity Full": vc("Connectivity_Level", "Full"),
        "Connectivity Partial": vc("Connectivity_Level", "Partial"),
        "Services Full": vc("Services_Level", "Full"),
        "Services Partial": vc("Services_Level", "Partial"),
        "Services None": vc("Services_Level", "None"),
        "Services Unverified": vc("Services_Level", "Unverified"),
        "Access Road only": vc("Access_Mode", "Road only"),
        "Access Road + Air": vc("Access_Mode", "Road + Air"),
        "Access No road or airstrip": vc("Access_Mode", "No road or airstrip"),
        "Access Air only": vc("Access_Mode", "Air only"),
        "School_No_Internet": int(com["School_No_Internet"].sum()),
        "Health_No_Internet": int(com["Health_No_Internet"].sum()),
        "Critical_To_Verify > 0": int((com["Critical_To_Verify_Count"] > 0).sum()),
        "Mean Service_Score (x100)": int(round(com["Service_Score"].mean() * 100)),
        "Level Critical": vc("Vulnerability_Level", "Critical"),
        "Level High": vc("Vulnerability_Level", "High"),
        "Level Medium": vc("Vulnerability_Level", "Medium"),
        "Level Low": vc("Vulnerability_Level", "Low"),
        "Manmoyi Dist_Health_km (x10)": int(round(com.loc[com["Community"] == "Manmoyi", "Dist_Health_km"].iat[0] * 10)),
    }
    if service_status is not None:
        a["ServiceStatus rows"] = len(service_status)
    if map_status is not None:
        a["MapStatus rows"] = len(map_status)
    return a


def validate(com, service_status=None, map_status=None, verbose=True) -> bool:
    act = actual_values(com, service_status, map_status)
    ok = True
    for k, v in act.items():
        exp = EXPECTED.get(k)
        good = exp == v
        ok &= good
        if verbose:
            print(f"  [{'OK' if good else 'MISMATCH'}] {k:<32} expected {exp!s:>6}  got {v!s:>6}")
    return ok


if __name__ == "__main__":
    from process_communities import build_communities
    from build_tables import build_service_status, build_map_status
    com = build_communities()
    passed = validate(com, build_service_status(com), build_map_status(com))
    print("\nAll checks passed - results match Power BI." if passed else "\nSome checks differ - see MISMATCH lines.")
