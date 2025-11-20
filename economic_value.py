import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

folder = os.path.dirname(__file__)
os.chdir(folder)

# ============================================================
# 1. Load annual yields (with particulate P/N and sediment grade)
#    and reuse-area potential, then merge
# ============================================================
yields = pd.read_csv("Output/Annual_Region_Yields.csv")
reuse = pd.read_csv("Output/Annual_Region_Reuse_Potential.csv")

# Merge on Year (reuse has ReuseArea_20t_ha)
annual = pd.merge(yields, reuse[["Year", "ReuseArea_20t_ha"]], on="Year", how="left")

# Protect reuse area
annual["ReuseArea_20t_ha"] = annual["ReuseArea_20t_ha"].fillna(0)


# ============================================================
# 2. Fertilizer & crop assumptions
# ============================================================
price_N = 1.89     # USD per kg N
price_P = 5.37     # USD per kg P
fert_N_need = 150  # kg N/ha demand
fert_P_need = 22   # kg P/ha demand

# Crop nutrient demand (g)
N_demand_g = fert_N_need * 1000
P_demand_g = fert_P_need * 1000

# Cost of conventional fertilizer (USD per ha)
cost_per_ha = fert_N_need * price_N + fert_P_need * price_P

# ============================================================
# 3. Recovery & availability parameters
#    Account for: processing recovery, N mineralization, P solubility
# ============================================================
recovery_efficiency = 0.8  # 80% recovery after processing
availability_N = 0.5      # 50% N available in-season (organic needs mineralization)
availability_P = 0.8      # 80% P available

# ============================================================
# 4. CRITICAL: Applied per-ha N/P on reuse area (NOT monitoring basis!)
#    Must use Total_N/P ÷ ReuseArea_20t_ha, NOT N_kg_ha_yr (monitoring basis)
# ============================================================
# Prefer sediment-bound recovered per-ha values (from Annual_Region_Yields)
# If available, these already represent particulate nutrient applied to a hectare at 20 t/ha
if "kgN_recovered_per_ha_20t" in annual.columns and "kgP_recovered_per_ha_20t" in annual.columns:
    annual["N_applied_kg_per_ha"] = annual["kgN_recovered_per_ha_20t"].fillna(0)
    annual["P_applied_kg_per_ha"] = annual["kgP_recovered_per_ha_20t"].fillna(0)
else:
    # Fallback: distribute total particulate mass across reuse area
    annual["ReuseArea_20t_ha_safe"] = annual["ReuseArea_20t_ha"].replace(0, np.nan)
    annual["N_applied_kg_per_ha"] = annual.get("Particulate_N_kg", annual.get("Total_N_kg", 0.0)) / annual["ReuseArea_20t_ha_safe"]
    annual["P_applied_kg_per_ha"] = annual.get("Particulate_P_kg", annual.get("Total_P_kg", 0.0)) / annual["ReuseArea_20t_ha_safe"]

# Usable N/P after recovery and availability fractions (apply physical factors)
annual["N_usable_kg_per_ha"] = annual["N_applied_kg_per_ha"] * recovery_efficiency * availability_N
annual["P_usable_kg_per_ha"] = annual["P_applied_kg_per_ha"] * recovery_efficiency * availability_P

# Clamp negatives
annual["N_usable_kg_per_ha"] = annual["N_usable_kg_per_ha"].clip(lower=0)
annual["P_usable_kg_per_ha"] = annual["P_usable_kg_per_ha"].clip(lower=0)

# ============================================================
# 5. Replacement rates (separate N and P)
# ============================================================
annual["Percent_saved_N"] = (
    annual["N_usable_kg_per_ha"] / fert_N_need
).clip(0, 1)

annual["Percent_saved_P"] = (
    annual["P_usable_kg_per_ha"] / fert_P_need
).clip(0, 1)

# ============================================================
# 6. Limiting nutrient (min(N, P))
# ============================================================
annual["Percent_saved_total"] = annual[["Percent_saved_N", "Percent_saved_P"]].min(axis=1)
annual["Percent_saved_total_pct"] = annual["Percent_saved_total"] * 100

# ============================================================
# 7. Economic value (two methods for transparency)
# ============================================================
# Method A: Limiting nutrient
annual["Cost_reduction_per_ha_limiting"] = annual["Percent_saved_total"] * cost_per_ha
annual["Cost_reduction_total_USD_limiting"] = (
    annual["Cost_reduction_per_ha_limiting"] * annual["ReuseArea_20t_ha"]
)

# Method B: Separate N/P pricing (MORE TRANSPARENT)
annual["N_saving_USD_per_ha"] = (
    annual["N_usable_kg_per_ha"].clip(upper=fert_N_need) * price_N
)
annual["P_saving_USD_per_ha"] = (
    annual["P_usable_kg_per_ha"].clip(upper=fert_P_need) * price_P
)
annual["Cost_reduction_per_ha"] = (
    annual["N_saving_USD_per_ha"] + annual["P_saving_USD_per_ha"]
)
annual["Cost_reduction_total_USD"] = (
    annual["Cost_reduction_per_ha"] * annual["ReuseArea_20t_ha"]
)

# ============================================================
# 7. Save output
# ============================================================
out_path = "Output/Annual_Region_Econ_Value.csv"
annual.to_csv(out_path, index=False)

# === 新增：输出经济分析年度数据到CSV，便于与图表匹配 ===
econ_trend_cols = [
    "Year", "ReuseArea_20t_ha",
    "N_applied_kg_per_ha", "P_applied_kg_per_ha",
    "N_usable_kg_per_ha", "P_usable_kg_per_ha",
    "Percent_saved_N", "Percent_saved_P", "Percent_saved_total",
    "Cost_reduction_per_ha", "Cost_reduction_total_USD",
    "Cost_reduction_per_ha_limiting", "Cost_reduction_total_USD_limiting",
    "gN_per_kg_sediment", "gP_per_kg_sediment",
    "kgN_recovered_per_ha_20t", "kgP_recovered_per_ha_20t"
]
annual[econ_trend_cols].to_csv("Output/Econ_Trend_Data.csv", index=False)
print("Created: Output/Econ_Trend_Data.csv")

print(f"Created: {out_path}")
print("\n=== Economics Summary ===")
print(annual[["Year", "ReuseArea_20t_ha", "N_applied_kg_per_ha", "P_applied_kg_per_ha",
              "N_usable_kg_per_ha", "P_usable_kg_per_ha",
              "Percent_saved_N", "Percent_saved_P",
              "Cost_reduction_total_USD"]].round(2))

# ============================================================
# 8. Trend plots
# ============================================================
plot_dir = "Output/Econ_Trend_Plots"
os.makedirs(plot_dir, exist_ok=True)

# --- 1. Total cost reduction (compare both methods) ---
plt.figure(figsize=(10,6))
plt.plot(annual["Year"], annual["Cost_reduction_total_USD_limiting"], marker="o", label="Limiting nutrient")
plt.plot(annual["Year"], annual["Cost_reduction_total_USD"], marker="s", label="By-price (recommended)")
plt.title("Annual Cost Reduction from Sediment Reuse (USD/year)")
plt.ylabel("USD/year")
plt.legend()
plt.grid()
plt.savefig(f"{plot_dir}/Cost_Reduction_Trend.png", dpi=300)
plt.close()

# --- 2. Limiting nutrient replacement ---
plt.figure(figsize=(10,6))
plt.plot(annual["Year"], annual["Percent_saved_total_pct"], marker="o", color="green")
plt.title("Annual % of Fertilizer Demand Replaced (Limiting Nutrient)")
plt.ylabel("% replaced")
plt.ylim(0, 100)
plt.grid()
plt.savefig(f"{plot_dir}/Percent_Replacement_Trend.png", dpi=300)
plt.close()

# --- 3. Separate N and P replacement ---
plt.figure(figsize=(10,6))
plt.plot(annual["Year"], annual["Percent_saved_N"]*100, marker="o", color="blue", label="N replaced")
plt.plot(annual["Year"], annual["Percent_saved_P"]*100, marker="o", color="orange", label="P replaced")
plt.title("Annual Replacement Rate for N and P (%)")
plt.ylabel("% replaced")
plt.ylim(0, 100)
plt.legend()
plt.grid()
plt.savefig(f"{plot_dir}/N_P_Replacement_Trend.png", dpi=300)
plt.close()

# --- 4. Cost reduction per hectare (by-price method) ---
plt.figure(figsize=(10,6))
plt.plot(annual["Year"], annual["Cost_reduction_per_ha"], marker="o", color="red")
plt.title("Cost Reduction per Hectare Applied (USD/ha/year)")
plt.ylabel("USD/ha/year")
plt.grid()
plt.savefig(f"{plot_dir}/Cost_Reduction_per_ha.png", dpi=300)
plt.close()

# --- 5. Applied N and P per hectare (new: shows the reuse-area basis) ---
plt.figure(figsize=(10,6))
plt.plot(annual["Year"], annual["N_applied_kg_per_ha"], marker="o", color="blue", label="N applied")
plt.plot(annual["Year"], annual["P_applied_kg_per_ha"], marker="o", color="orange", label="P applied")
plt.axhline(y=fert_N_need, color="blue", linestyle="--", alpha=0.5, label=f"N demand ({fert_N_need} kg/ha)")
plt.axhline(y=fert_P_need, color="orange", linestyle="--", alpha=0.5, label=f"P demand ({fert_P_need} kg/ha)")
plt.title("Applied N and P per Hectare (from sediment reuse)")
plt.ylabel("kg/ha")
plt.legend()
plt.grid()
plt.savefig(f"{plot_dir}/Applied_NP_Trend.png", dpi=300)
plt.close()

# --- 6. Sediment grade (g nutrient per kg sediment) ---
plt.figure(figsize=(10,6))
if "gN_per_kg_sediment" in annual.columns:
    plt.plot(annual["Year"], annual["gN_per_kg_sediment"], marker="o", color="green", label="gN per kg sediment")
if "gP_per_kg_sediment" in annual.columns:
    plt.plot(annual["Year"], annual["gP_per_kg_sediment"], marker="s", color="purple", label="gP per kg sediment")
plt.title("Sediment Grade: Nutrient per kg Sediment (g/kg)")
plt.ylabel("g nutrient / kg sediment")
plt.legend()
plt.grid()
plt.savefig(f"{plot_dir}/Sediment_Grade_Trend.png", dpi=300)
plt.close()

# --- 7. Recovered N/P per hectare at 20 t/ha ---
plt.figure(figsize=(10,6))
if "kgN_recovered_per_ha_20t" in annual.columns:
    plt.plot(annual["Year"], annual["kgN_recovered_per_ha_20t"], marker="o", color="blue", label="kgN recovered/ha @20t")
if "kgP_recovered_per_ha_20t" in annual.columns:
    plt.plot(annual["Year"], annual["kgP_recovered_per_ha_20t"], marker="s", color="orange", label="kgP recovered/ha @20t")
plt.title("Recovered N and P per Hectare at 20 t/ha (kg/ha)")
plt.ylabel("kg/ha")
plt.legend()
plt.grid()
plt.savefig(f"{plot_dir}/Recovered_NP_per_ha_20t.png", dpi=300)
plt.close()

# --- 8. Percent of crop demand met by recovered nutrients (after availability) ---
plt.figure(figsize=(10,6))
plt.plot(annual["Year"], (annual["N_usable_kg_per_ha"]/fert_N_need)*100, marker="o", color="blue", label="% N demand met")
plt.plot(annual["Year"], (annual["P_usable_kg_per_ha"]/fert_P_need)*100, marker="o", color="orange", label="% P demand met")
plt.title("Percent of Crop Nutrient Demand Met by Recovered Nutrients (after availability)")
plt.ylabel("% of demand")
plt.ylim(0, 200)
plt.legend()
plt.grid()
plt.savefig(f"{plot_dir}/Recovered_NP_pct_demand_20t.png", dpi=300)
plt.close()

print(f"Saved plots to: {plot_dir}")
