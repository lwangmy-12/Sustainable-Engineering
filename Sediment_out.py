# ============================================================
# Sediment_out.py
# Author: Mingyu Wang
# Purpose: Calculate annual sediment and nutrient loads (kg/ha/year)
#          for Great Lakes USGS Edge-of-Field sites
# ============================================================

import pandas as pd
import numpy as np
import os

# ------------------------------------------------------------
# STEP 0. Set working directory (current folder)
# ------------------------------------------------------------
# If this file is saved in the same folder as your CSVs, this will work automatically
folder = os.path.dirname(__file__)
os.chdir(folder)

# ------------------------------------------------------------
# STEP 1. Load datasets
# ------------------------------------------------------------
sites = pd.read_csv("RAW/EOF_Site_Table.csv", encoding="latin1")
storm_rain = pd.read_csv("RAW/All_EOF_StormEventLoadsRainCalculated.csv", encoding="latin1")

# ------------------------------------------------------------
# STEP 2. Filter Great Lakes States
# ------------------------------------------------------------
great_lakes_states = ["OH", "MI", "IN", "WI", "NY"]
sites_gl = sites[sites["State"].isin(great_lakes_states)]

print(f" Number of selected sites in Great Lakes region: {len(sites_gl)}")

sites_gl = sites_gl[["USGS_Station_Number", "State", "Area", "Site_Type"]]

# ------------------------------------------------------------
# STEP 3. Filter rainfall + load events for these sites
# ------------------------------------------------------------
storm_gl = storm_rain[storm_rain["USGS_Station_Number"].isin(sites_gl["USGS_Station_Number"])]
print(f" Number of storm events retained: {len(storm_gl)}")

# ------------------------------------------------------------
# STEP 4. Extract year and calculate annual totals
# ------------------------------------------------------------
storm_gl["Year"] = pd.to_datetime(storm_gl["storm_start"], errors="coerce").dt.year

load_cols = [
    "USGS_Station_Number",
    "Year",
    "suspended_sediment_yield_pounds_per_acre",
    "total_nitrogen_yield_pounds_per_acre",
    "total_phosphorus_unfiltered_yield_pounds_per_acre"
]
storm_gl = storm_gl[load_cols].dropna(subset=["Year"])

annual_loads = (
    storm_gl.groupby(["USGS_Station_Number", "Year"])
    .sum(numeric_only=True)
    .reset_index()
)

# ------------------------------------------------------------
# STEP 5. Convert units and merge with site info
# ------------------------------------------------------------
# 1 pound/acre = 1.12085 kg/ha
factor = 1.12085
annual_loads["Sediment_kg_ha_yr"] = annual_loads["suspended_sediment_yield_pounds_per_acre"] * factor
annual_loads["N_kg_ha_yr"] = annual_loads["total_nitrogen_yield_pounds_per_acre"] * factor
annual_loads["P_kg_ha_yr"] = annual_loads["total_phosphorus_unfiltered_yield_pounds_per_acre"] * factor

annual_loads = annual_loads.merge(sites_gl, on="USGS_Station_Number", how="left")

# ------------------------------------------------------------
# STEP 6. Calculate mean annual yield by state
# ------------------------------------------------------------
state_summary = (
    annual_loads.groupby("State")[["Sediment_kg_ha_yr", "N_kg_ha_yr", "P_kg_ha_yr"]]
    .mean()
    .reset_index()
)

# ------------------------------------------------------------
# STEP 7. Export results
# ------------------------------------------------------------
annual_loads.to_csv("Output/Annual_Sediment_Nutrient_Loads.csv", index=False)
state_summary.to_csv("Output/State_Average_Annual_Yields.csv", index=False)

print("\n Processing finished successfully!")
print("  Created: Annual_Sediment_Nutrient_Loads.csv")
print("  Created: State_Average_Annual_Yields.csv\n")

print("Preview of per-state averages:")
print(state_summary)



# ============================================================
# STEP 8. Plot temporal trends (Sediment, N, P) by state
# ============================================================

import matplotlib.pyplot as plt

# ------------------------------------------------------------
# Load the annual results (created earlier)
# ------------------------------------------------------------
annual_loads = pd.read_csv("Output/Annual_Sediment_Nutrient_Loads.csv")

# Make sure Year column is integer
annual_loads["Year"] = annual_loads["Year"].astype(int)

# output folder
out_folder = "Output"

# ------------------------------------------------------------
# Define a reusable plotting function
# ------------------------------------------------------------
def plot_trend(data, value_col, ylabel, title, filename):
    """
    Plot the temporal trend of a given nutrient (or sediment) per state.
    
    Parameters:
        data: DataFrame containing 'State', 'Year', and the value column
        value_col: str, column name to plot (e.g., 'Sediment_kg_ha_yr')
        ylabel: str, label for y-axis
        title: str, plot title
        filename: str, output PNG file name
    """
    plt.figure(figsize=(10,6))
    
    # Group by State and Year to calculate mean across sites
    summary = data.groupby(["State", "Year"])[value_col].mean().reset_index()
    
    # Pivot to get Year as x-axis and states as columns
    pivot = summary.pivot(index="Year", columns="State", values=value_col)
    
    # Plot each state's line
    pivot.plot(ax=plt.gca(), marker="o", linewidth=2)
    
    plt.title(title, fontsize=14, weight="bold")
    plt.xlabel("Year", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(title="State", fontsize=10)
    plt.xticks(pivot.index, rotation=45)
    plt.tight_layout()
    
    # Save the figure as PNG
    plt.savefig(os.path.join(out_folder, filename), dpi=300)
    plt.close()
    print(f" Saved figure: {filename}")

# ------------------------------------------------------------
# STEP 9. Generate three separate plots
# ------------------------------------------------------------
plot_trend(
    annual_loads,
    "Sediment_kg_ha_yr",
    "Sediment yield (kg/ha/year)",
    "Annual Sediment Yield by State",
    "Sediment_trend.png"
)

plot_trend(
    annual_loads,
    "N_kg_ha_yr",
    "Nitrogen yield (kg/ha/year)",
    "Annual Nitrogen Yield by State",
    "N_trend.png"
)

plot_trend(
    annual_loads,
    "P_kg_ha_yr",
    "Phosphorus yield (kg/ha/year)",
    "Annual Phosphorus Yield by State",
    "P_trend.png"
)

print("\n Trend plots created successfully!")
