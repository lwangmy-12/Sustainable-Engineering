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
# 3.a Estimate particulate (sediment-associated) P and N
# ------------------------------------------------------------
# Columns available in dataset for improved partitioning
orthophosphate_col = "orthophosphate_conc_mgL"  # dissolved reactive P (PO4) - stays in solution
tkn_col = "total_Kjeldahl_nitrogen_unfiltered_conc_mgL"  # mostly particulate organic N + ammonium
ammonia_col = "ammonia_plus_ammonium_conc_mgL"  # dissolved inorganic N (NH3/NH4)

# Particulate P conc (mg/L) approximated as total_unfiltered - orthophosphate
if orthophosphate_col in events.columns:
    events["Particulate_P_conc_mgL"] = (events[P_conc].fillna(0) - events[orthophosphate_col].fillna(0)).clip(lower=0)
else:
    # fallback: assume all P is particulate (conservative) if orthophosphate missing
    events["Particulate_P_conc_mgL"] = events[P_conc].fillna(0)

# Particulate N conc (mg/L) approximated as TKN - ammonia (dissolved inorganic)
if tkn_col in events.columns and ammonia_col in events.columns:
    events["Particulate_N_conc_mgL"] = (events[tkn_col].fillna(0) - events[ammonia_col].fillna(0)).clip(lower=0)
else:
    # fallback: use total N concentration as an upper-bound
    events["Particulate_N_conc_mgL"] = events[N_conc].fillna(0)

# Particulate masses per event (mg -> kg)
events["Particulate_P_mass_mg"] = events["Particulate_P_conc_mgL"] * Q
events["Particulate_N_mass_mg"] = events["Particulate_N_conc_mgL"] * Q
events["Particulate_P_mass_kg"] = events["Particulate_P_mass_mg"] / 1e6
events["Particulate_N_mass_kg"] = events["Particulate_N_mass_mg"] / 1e6

# Optional: particulate grams per kg sediment at event level (useful diagnostic)
events["gP_per_kg_sediment_event"] = np.where(
    events["Sediment_load_kg"] > 0,
    events["Particulate_P_mass_kg"] / events["Sediment_load_kg"] * 1000.0,
    np.nan
)
events["gN_per_kg_sediment_event"] = np.where(
    events["Sediment_load_kg"] > 0,
    events["Particulate_N_mass_kg"] / events["Sediment_load_kg"] * 1000.0,
    np.nan
)

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
    "Particulate_P_mass_kg": "sum",
    "Particulate_N_mass_kg": "sum",
    "Area_ha": "first"
})

# ------------------------------------------------------------
# 5.1 Identify VALID station-year PER PARAMETER
# ------------------------------------------------------------
# Check if a station has valid data for each specific parameter in that year.
# We use count() > 0: if there is at least one event with concentration data, it's valid.
validity_check = df.groupby(["USGS_Station_Number", "Year"], as_index=False)[[P_conc, N_conc, sed_conc]].count()

# Rename columns to be clear boolean flags
validity_check["Valid_P"] = validity_check[P_conc] > 0
validity_check["Valid_N"] = validity_check[N_conc] > 0
validity_check["Valid_Sed"] = validity_check[sed_conc] > 0

# Merge these flags back into the annual dataframe
annual = annual.merge(
    validity_check[["USGS_Station_Number", "Year", "Valid_P", "Valid_N", "Valid_Sed"]],
    on=["USGS_Station_Number", "Year"],
    how="left"
)

# Fill NaN flags with False (safe fallback)
annual["Valid_P"] = annual["Valid_P"].fillna(False)
annual["Valid_N"] = annual["Valid_N"].fillna(False)
annual["Valid_Sed"] = annual["Valid_Sed"].fillna(False)

# ------------------------------------------------------------
# 6. Annual regional totals using parameter-specific valid areas
# ------------------------------------------------------------
years = sorted(annual["Year"].unique())
rows = []

for y in years:
    sub = annual[annual["Year"] == y]
    
    if len(sub) == 0:
        continue

    # --- 1. Sediment Calculation ---
    # Only sum mass and area for stations with valid sediment data
    sub_sed = sub[sub["Valid_Sed"]]
    eff_area_sed = sub_sed["Area_ha"].sum()
    total_sed = sub_sed["Sediment_load_kg"].sum()
    # Calculate Yield
    sed_per_ha = total_sed / eff_area_sed if eff_area_sed > 0 else None

    # --- 2. Nitrogen Calculation ---
    # Only sum mass and area for stations with valid N data
    sub_N = sub[sub["Valid_N"]]
    eff_area_N = sub_N["Area_ha"].sum()
    total_N = sub_N["N_mass_kg"].sum()
    total_particulate_N = sub_N["Particulate_N_mass_kg"].sum() if "Particulate_N_mass_kg" in sub.columns else 0.0
    # Calculate Yield
    N_per_ha = total_N / eff_area_N if eff_area_N > 0 else None

    # --- 3. Phosphorus Calculation ---
    # Only sum mass and area for stations with valid P data
    sub_P = sub[sub["Valid_P"]]
    eff_area_P = sub_P["Area_ha"].sum()
    total_P = sub_P["P_mass_kg"].sum()
    total_particulate_P = sub_P["Particulate_P_mass_kg"].sum() if "Particulate_P_mass_kg" in sub.columns else 0.0
    # Calculate Yield
    P_per_ha = total_P / eff_area_P if eff_area_P > 0 else None
    
    # Note: We store eff_area_sed as the "primary" effective area for reference, 
    # but N and P yields are calculated using their own specific areas.
    rows.append({
        "Year": y,
        "Effective_Area_ha": eff_area_sed, 
        "Effective_Area_N_ha": eff_area_N, # Useful for debugging
        "Effective_Area_P_ha": eff_area_P, # Useful for debugging
        "Total_Sediment_kg": total_sed,
        "Total_N_kg": total_N,
        "Total_P_kg": total_P,
        "Particulate_P_kg": total_particulate_P,
        "Particulate_N_kg": total_particulate_N,
        "Sediment_kg_ha_yr": sed_per_ha,
        "N_kg_ha_yr": N_per_ha,
        "P_kg_ha_yr": P_per_ha
    })

annual_region = pd.DataFrame(rows)

# ------------------------------------------------------------
# 6.a Compute sediment "grade" (sediment-bound nutrient per dry mass)
# Standardized to g nutrient per kg sediment (g/kg), and per-ha at 20 t/ha dose
# ------------------------------------------------------------
dose_kg_per_ha = 20000.0  # 20 t/ha
annual_region["gP_per_kg_sediment"] = np.where(
    annual_region["Total_Sediment_kg"] > 0,
    annual_region["Particulate_P_kg"] / annual_region["Total_Sediment_kg"] * 1000.0,
    np.nan
)
annual_region["gN_per_kg_sediment"] = np.where(
    annual_region["Total_Sediment_kg"] > 0,
    annual_region["Particulate_N_kg"] / annual_region["Total_Sediment_kg"] * 1000.0,
    np.nan
)

# Recovered per hectare at 20 t/ha (g/ha and kg/ha)
annual_region["gP_recovered_per_ha_20t"] = annual_region["gP_per_kg_sediment"] * dose_kg_per_ha
annual_region["kgP_recovered_per_ha_20t"] = annual_region["gP_recovered_per_ha_20t"] / 1000.0
annual_region["gN_recovered_per_ha_20t"] = annual_region["gN_per_kg_sediment"] * dose_kg_per_ha
annual_region["kgN_recovered_per_ha_20t"] = annual_region["gN_recovered_per_ha_20t"] / 1000.0

# --- Particulate P/N yield trend (line plot) (kg/ha/year) ---
annual_region["Particulate_P_kg_ha_yr"] = np.where(
    annual_region["Effective_Area_ha"] > 0,
    annual_region["Particulate_P_kg"] / annual_region["Effective_Area_ha"],
    np.nan
)
annual_region["Particulate_N_kg_ha_yr"] = np.where(
    annual_region["Effective_Area_ha"] > 0,
    annual_region["Particulate_N_kg"] / annual_region["Effective_Area_ha"],
    np.nan
)


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

# --- Particulate P/N total trend (line plot) ---
plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["Particulate_P_kg"], marker="o", color="purple", label="Particulate P (kg)")
plt.plot(annual_region["Year"], annual_region["Particulate_N_kg"], marker="o", color="green", label="Particulate N (kg)")
plt.title("Annual Total Particulate Phosphorus and Nitrogen (kg/year)")
plt.ylabel("kg/year")
plt.legend()
plt.grid()
plt.savefig("Output/Particulate_PN_Total_Trend.png", dpi=300)
plt.close()

# --- Particulate P/N yield trend (line plot)（kg/ha/year）---
plt.figure(figsize=(10,6))
plt.plot(annual_region["Year"], annual_region["Particulate_P_kg_ha_yr"], marker="o", color="purple", label="Particulate P Yield (kg/ha/year)")
plt.plot(annual_region["Year"], annual_region["Particulate_N_kg_ha_yr"], marker="o", color="green", label="Particulate N Yield (kg/ha/year)")
plt.title("Annual Particulate P and N Yield (kg/ha/year)")
plt.ylabel("kg/ha/year")
plt.legend()
plt.grid()
plt.savefig("Output/Particulate_PN_Yield_Trend.png", dpi=300)
plt.close()

# --- Sediment grade bar chart (g/kg, per year) ---
plt.figure(figsize=(10,6))
bar_width = 0.4
years = annual_region["Year"]
plt.bar(years - bar_width/2, annual_region["gP_per_kg_sediment"], width=bar_width, color="purple", label="gP/kg sediment")
plt.bar(years + bar_width/2, annual_region["gN_per_kg_sediment"], width=bar_width, color="green", label="gN/kg sediment")
plt.title("Sediment Grade: Particulate P and N per kg Sediment (g/kg)")
plt.ylabel("g nutrient / kg sediment")
plt.legend()
plt.grid()
plt.savefig("Output/Sediment_Grade_Bar.png", dpi=300)
plt.close()
