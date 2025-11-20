import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Set working directory to script location
folder = os.path.dirname(__file__)
os.chdir(folder)

# ============================================================
# 1. Load and Preprocess Data
# ============================================================
print("Loading data...")
events = pd.read_csv("RAW/All_EOF_StormEventLoadsRainCalculated.csv")

# --- Parse Years ---
storm_cols = [c for c in events.columns if ("storm" in c.lower() and "start" in c.lower())]
if len(storm_cols) == 0:
    date_candidates = [c for c in events.columns if "date" in c.lower()]
    storm_col = date_candidates[0]
else:
    storm_col = storm_cols[0]

events[storm_col] = pd.to_datetime(events[storm_col], errors="coerce")
events["Year"] = events[storm_col].dt.year

# Unit conversions: Pounds to kg
events["Sediment_load_kg"] = events["suspended_sediment_load_pounds"] * 0.45359237
Q = events["runoff_volume"] # Liters

# ------------------------------------------------------------
# 2. Calculate Particulate Nutrients (Mass)
# ------------------------------------------------------------
P_conc = "total_phosphorus_unfiltered_conc_mgL"
N_conc = "total_nitrogen_conc_mgL"
orthophosphate_col = "orthophosphate_conc_mgL" 
tkn_col = "total_Kjeldahl_nitrogen_unfiltered_conc_mgL"
ammonia_col = "ammonia_plus_ammonium_conc_mgL"

# 2.1 Particulate P
if orthophosphate_col in events.columns:
    events["Particulate_P_conc_mgL"] = (events[P_conc].fillna(0) - events[orthophosphate_col].fillna(0)).clip(lower=0)
else:
    events["Particulate_P_conc_mgL"] = events[P_conc].fillna(0)

# 2.2 Particulate N
if tkn_col in events.columns and ammonia_col in events.columns:
    events["Particulate_N_conc_mgL"] = (events[tkn_col].fillna(0) - events[ammonia_col].fillna(0)).clip(lower=0)
else:
    events["Particulate_N_conc_mgL"] = events[N_conc].fillna(0)

# Calculate Mass (kg)
events["Particulate_P_mass_kg"] = (events["Particulate_P_conc_mgL"] * Q) / 1e6
events["Particulate_N_mass_kg"] = (events["Particulate_N_conc_mgL"] * Q) / 1e6

# ============================================================
# 3. Site-Specific Aggregation
# ============================================================
site_stats = events.groupby("USGS_Station_Number").agg({
    "Sediment_load_kg": "sum",
    "Particulate_P_mass_kg": "sum",
    "Particulate_N_mass_kg": "sum",
    "storm_start": "count",
    "Year": "nunique"
}).rename(columns={"storm_start": "Event_Count", "Year": "Years_Monitored"})

# Filter: Only keep sites with > 100kg total load
site_stats = site_stats[site_stats["Sediment_load_kg"] > 100].copy()

# --- Calculate Avg Annual Load (Supply) ---
site_stats["Avg_Annual_Load_kg"] = site_stats["Sediment_load_kg"] / site_stats["Years_Monitored"]

# ============================================================
# 4. Calculate "Grade" (Nutrient Content)
# ============================================================
site_stats["Grade_N_g_kg"] = (site_stats["Particulate_N_mass_kg"] / site_stats["Sediment_load_kg"]) * 1000
site_stats["Grade_P_g_kg"] = (site_stats["Particulate_P_mass_kg"] / site_stats["Sediment_load_kg"]) * 1000

# ============================================================
# 5. Economic Valuation (Dynamic P-Limit)
# ============================================================
PRICE_N = 1.89          
PRICE_P = 5.37          
FERT_N_NEED = 150       
FERT_P_NEED = 22        
AVAIL_N = 0.4
AVAIL_P = 0.8

# Step A: Effective P content
site_stats["Effective_P_content"] = (site_stats["Grade_P_g_kg"] / 1000) * AVAIL_P

# Step B: Max Allowed Dose (P-Limit)
site_stats["Max_Allowed_Dose_kg_ha"] = np.where(
    site_stats["Effective_P_content"] > 0,
    FERT_P_NEED / site_stats["Effective_P_content"],
    0
)

# Step C: Physical Limit (100 tons/ha)
PHYSICAL_LIMIT_KG = 100000 
site_stats["Optimized_Dose_kg_ha"] = site_stats["Max_Allowed_Dose_kg_ha"].clip(upper=PHYSICAL_LIMIT_KG)

# --- NEW: Calculate Reuse Area (Supply / Dose) ---
# "How many hectares can I cover per year with this optimized dose?"
site_stats["Potential_Reuse_Area_ha"] = np.where(
    site_stats["Optimized_Dose_kg_ha"] > 0,
    site_stats["Avg_Annual_Load_kg"] / site_stats["Optimized_Dose_kg_ha"],
    0
)

# Step D: Calculate Applied Nutrients
site_stats["N_Applied_Optimized"] = (site_stats["Grade_N_g_kg"] / 1000) * site_stats["Optimized_Dose_kg_ha"]
site_stats["P_Applied_Optimized"] = (site_stats["Grade_P_g_kg"] / 1000) * site_stats["Optimized_Dose_kg_ha"]

# Step E: Available Nutrients
site_stats["N_Available_kg_ha"] = site_stats["N_Applied_Optimized"] * AVAIL_N
site_stats["P_Available_kg_ha"] = site_stats["P_Applied_Optimized"] * AVAIL_P

# Step F: Economic Value ($)
site_stats["Value_N_USD_ha"] = site_stats["N_Available_kg_ha"].clip(upper=FERT_N_NEED) * PRICE_N
site_stats["Value_P_USD_ha"] = site_stats["P_Available_kg_ha"].clip(upper=FERT_P_NEED) * PRICE_P
site_stats["Total_Value_USD_ha"] = site_stats["Value_N_USD_ha"] + site_stats["Value_P_USD_ha"]

# ============================================================
# 6. Sorting and Output
# ============================================================
site_stats = site_stats.sort_values("Total_Value_USD_ha", ascending=False)
site_stats["Rank"] = range(1, len(site_stats) + 1)

os.makedirs("Output", exist_ok=True)

output_cols = [
    "Rank", 
    "Years_Monitored",
    "Avg_Annual_Load_kg",         # (Supply Mass)
    "Optimized_Dose_kg_ha",       #  (Demand per ha)
    "Potential_Reuse_Area_ha",    #  (Supply Area) <--- NEW!
    "Total_Value_USD_ha",         #  (Value per ha)
    "Grade_N_g_kg", 
    "Grade_P_g_kg"
]

site_stats[output_cols].to_csv("Output/Site_Specific_Economics.csv")
print("Created: Output/Site_Specific_Economics.csv")
print("\n=== Top 5 High-Value Sites ===")
print(site_stats[output_cols].head(5).to_string()) # to_string helps formatting

# ============================================================
# 7. Visualizations
# ============================================================
top_sites = site_stats.head(15)
site_ids = top_sites.index.astype(str)

# Plot 1: Value ($/ha)
plt.figure(figsize=(12, 6))
plt.bar(site_ids, top_sites["Value_N_USD_ha"], label="Nitrogen Value", color="#2ca02c")
plt.bar(site_ids, top_sites["Value_P_USD_ha"], bottom=top_sites["Value_N_USD_ha"], label="Phosphorus Value", color="#1f77b4")
plt.title("Top 15 Sites: Economic Value ($/ha) at Optimized Dose")
plt.ylabel("USD / ha")
plt.xticks(rotation=45, ha="right")
plt.legend()
plt.tight_layout()
plt.savefig("Output/Top_Sites_Economic_Value.png", dpi=300)
plt.close()

# Plot 2: Sediment Grade (g nutrient/kg)
plt.figure(figsize=(12, 6))
bar_width = 0.4
plt.bar(site_ids, top_sites["Grade_P_g_kg"], width=bar_width, color="purple", label="gP/kg sediment")
plt.bar(site_ids, top_sites["Grade_N_g_kg"], width=bar_width, color="green", alpha=0.5, label="gN/kg sediment", bottom=top_sites["Grade_P_g_kg"])
plt.title("Top 15 Sites: Sediment Grade (g nutrient/kg)")
plt.ylabel("g nutrient / kg sediment")
plt.xticks(rotation=45, ha="right")
plt.legend()
plt.tight_layout()
plt.savefig("Output/Top_Sites_Sediment_Grade.png", dpi=300)
plt.close()

# Plot 3: Percent Replacement for Top Site (Best Case Scenario)
# Calculate replacement % for the #1 ranked site
best_site = top_sites.iloc[0]
pct_N_replaced = (best_site["N_Available_kg_ha"] / FERT_N_NEED) * 100
pct_P_replaced = (best_site["P_Available_kg_ha"] / FERT_P_NEED) * 100

plt.figure(figsize=(6, 6))
plt.bar(["Nitrogen", "Phosphorus"], [pct_N_replaced, pct_P_replaced], color=["#2ca02c", "#1f77b4"])
plt.title(f"Nutrient Replacement Potential\nTop Site: {best_site.name}")
plt.ylabel("% of Crop Demand Met")
plt.ylim(0, 100) # Usually top sites can meet significant demand
plt.grid(axis="y", linestyle="--", alpha=0.5)
for i, v in enumerate([pct_N_replaced, pct_P_replaced]):
    plt.text(i, v + 1, f"{v:.1f}%", ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig("Output/Top_Site_Replacement_Pct.png", dpi=300)
plt.close()

print("Saved plots: Top_Sites_Economic_Value.png, Top_Sites_Sediment_Grade.png, Top_Site_Replacement_Pct.png")