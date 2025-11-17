import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

folder = os.path.dirname(__file__)
os.chdir(folder)

# ============================================================
# 1. Load conc-based annual mass + reuse area
# ============================================================
annual = pd.read_csv("Output/Annual_Region_Reuse_Potential.csv")

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
availability_N = 0.5       # 50% N available in-season (organic needs mineralization)
availability_P = 0.8       # 80% P available

# ============================================================
# 4. CRITICAL: Applied per-ha N/P on reuse area (NOT monitoring basis!)
#    Must use Total_N/P ÷ ReuseArea_20t_ha, NOT N_kg_ha_yr (monitoring basis)
# ============================================================
# Protect against division by zero
annual["ReuseArea_20t_ha_safe"] = annual["ReuseArea_20t_ha"].replace(0, np.nan)

# Applied per hectare (kg/ha) - CORRECT BASIS
annual["N_applied_kg_per_ha"] = annual["Total_N_kg"] / annual["ReuseArea_20t_ha_safe"]
annual["P_applied_kg_per_ha"] = annual["Total_P_kg"] / annual["ReuseArea_20t_ha_safe"]

# Usable N/P after recovery and availability fractions
annual["N_usable_kg_per_ha"] = (
    annual["N_applied_kg_per_ha"] * recovery_efficiency * availability_N
)
annual["P_usable_kg_per_ha"] = (
    annual["P_applied_kg_per_ha"] * recovery_efficiency * availability_P
)

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

print(f"Saved plots to: {plot_dir}")
