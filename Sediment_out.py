import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

folder = os.path.dirname(__file__)
os.chdir(folder)

# ------------------------------------------------------------
# 1. Load files
# ------------------------------------------------------------
events = pd.read_csv("RAW/All_EOF_StormEventLoadsRainCalculated.csv")
sites  = pd.read_csv("RAW/EOF_Site_Table.csv", encoding="latin1")

# Convert area to hectares (correct value)
sites["Area_ha"] = sites["Area"] * 0.4046856

# ------------------------------------------------------------
# 2. Identify storm start date column
# ------------------------------------------------------------
storm_cols = [c for c in events.columns if ("storm" in c.lower() and "start" in c.lower())]

if len(storm_cols) == 0:
    date_candidates = [c for c in events.columns if "date" in c.lower()]
    if len(date_candidates) == 0:
        raise ValueError("No storm_start or date column found.")
    storm_col = date_candidates[0]
else:
    storm_col = storm_cols[0]

events[storm_col] = pd.to_datetime(events[storm_col], errors="coerce")
events["Year"]     = events[storm_col].dt.year

# ------------------------------------------------------------
# 3. Concentration-based nutrient mass computation
# ------------------------------------------------------------
# Required concentration fields
P_conc = "total_phosphorus_unfiltered_conc_mgL"
N_conc = "total_nitrogen_conc_mgL"
sed_conc = "suspended_sediment_conc_mgL"

# Sediment load field (in pounds → convert to kg)
events["Sediment_load_kg"] = events["suspended_sediment_load_pounds"] * 0.45359237

# runoff_volume is already in Liters
Q = events["runoff_volume"]

# Nutrient mass (mg) = concentration (mg/L) × runoff volume (L)
events["P_mass_mg"] = events[P_conc] * Q
events["N_mass_mg"] = events[N_conc] * Q

# Convert mg → kg
events["P_mass_kg"] = events["P_mass_mg"] / 1e6
events["N_mass_kg"] = events["N_mass_mg"] / 1e6

# ------------------------------------------------------------
# 4. Merge site area
# ------------------------------------------------------------
df = events.merge(
    sites[["USGS_Station_Number","Area_ha"]],
    on="USGS_Station_Number",
    how="left"
)

# ------------------------------------------------------------
# 5. Aggregate per station-year (sum of kg, NOT kg/ha)
# ------------------------------------------------------------
annual = df.groupby(["USGS_Station_Number","Year"], as_index=False).agg({
    "Sediment_load_kg": "sum",
    "P_mass_kg": "sum",
    "N_mass_kg": "sum",
    "Area_ha": "first"
})

# ------------------------------------------------------------
# 5.1 Identify VALID station-year
# If both P and N concentrations missing → invalid
# ------------------------------------------------------------
annual["Valid"] = ~(
    df.groupby(["USGS_Station_Number","Year"])[[P_conc, N_conc]].mean().isna().all(axis=1)
).values

# Keep valid rows only (important!)
annual_valid = annual[annual["Valid"]]

# ------------------------------------------------------------
# 6. Annual regional totals using only valid stations in that year
# ------------------------------------------------------------
# Use VALID years only (from data that passed QC)
years = sorted(annual_valid["Year"].dropna().unique())
rows   = []

for y in years:
    sub = annual_valid[annual_valid["Year"] == y]

    if len(sub) == 0:
        rows.append({
            "Year": y,
            "Effective_Area_ha": 0,
            "Total_Sediment_kg": 0,
            "Total_N_kg": 0,
            "Total_P_kg": 0,
            "Sediment_kg_ha_yr": None,
            "N_kg_ha_yr": None,
            "P_kg_ha_yr": None
        })
        continue

    # total area = area of valid stations
    effective_area = sub["Area_ha"].sum()

    total_sed = sub["Sediment_load_kg"].sum()
    total_N   = sub["N_mass_kg"].sum()
    total_P   = sub["P_mass_kg"].sum()

    sed_per_ha = total_sed / effective_area if effective_area > 0 else None
    N_per_ha   = total_N   / effective_area if effective_area > 0 else None
    P_per_ha   = total_P   / effective_area if effective_area > 0 else None

    rows.append({
        "Year": y,
        "Effective_Area_ha": effective_area,
        "Total_Sediment_kg": total_sed,
        "Total_N_kg": total_N,
        "Total_P_kg": total_P,
        "Sediment_kg_ha_yr": sed_per_ha,
        "N_kg_ha_yr": N_per_ha,
        "P_kg_ha_yr": P_per_ha
    })

annual_region = pd.DataFrame(rows)

annual_region.to_csv("Output/Annual_Region_Yields.csv", index=False)
print("Created: Annual_Region_Yields.csv")
print(annual_region.head())

# ------------------------------------------------------------
# 7. Trend plots (Total and per-ha)
# ------------------------------------------------------------
plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["Total_Sediment_kg"], marker="o")
plt.title("Annual Total Sediment (kg/year)")
plt.ylabel("kg")
plt.grid()
plt.savefig("Output/Sediment_Total_Trend.png", dpi=300)
plt.close()

plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["Sediment_kg_ha_yr"], marker="o", color="red")
plt.title("Annual Sediment Yield (kg/ha/year)")
plt.ylabel("kg/ha")
plt.grid()
plt.savefig("Output/Sediment_Yield_Trend.png", dpi=300)
plt.close()

plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["Total_N_kg"], marker="o", color="orange")
plt.title("Annual Total Nitrogen (kg/year)")
plt.ylabel("kg")
plt.grid()
plt.savefig("Output/N_Total_Trend.png", dpi=300)
plt.close()

plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["N_kg_ha_yr"], marker="o", color="green")
plt.title("Annual Nitrogen Yield (kg/ha/year)")
plt.ylabel("kg/ha")
plt.grid()
plt.savefig("Output/N_Yield_Trend.png", dpi=300)
plt.close()

plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["Total_P_kg"], marker="o", color="blue")
plt.title("Annual Total Phosphorus (kg/year)")
plt.ylabel("kg")
plt.grid()
plt.savefig("Output/P_Total_Trend.png", dpi=300)
plt.close()

plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["P_kg_ha_yr"], marker="o", color="purple")
plt.title("Annual Phosphorus Yield (kg/ha/year)")
plt.ylabel("kg/ha")
plt.grid()
plt.savefig("Output/P_Yield_Trend.png", dpi=300)
plt.close()

print("Saved all annual trend plots.")
