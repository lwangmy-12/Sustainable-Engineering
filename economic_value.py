import pandas as pd
import os

folder = os.path.dirname(__file__)
os.chdir(folder)

# ---- Inputs from previous steps ----
df = pd.read_csv("Output/Sediment_Reuse_Potential_by_State.csv")

# ---- Assumptions (Need to refine with USDA sources!!!???) ----
price_N = 1.89    # USD per kg of N (assumed, google search)
price_P = 5.37    # USD per kg of P (assumed, google search)
fert_N_need = 150  # kg N / ha typical demand (assumed, google search)
fert_P_need = 22   # kg P / ha typical demand (assumed, google search)

# Application doses from Braga et al. (kg/ha)
doses = {
    "5t":  5000, # After find N and P is rich in sidement, to get more econimic value (Assumed)
    #Original:
    "20t":  20000,
    "50t":  50000,
    "75t":  75000,
    "100t": 100000
}

# ---- 1) Area-weighted production: total sediment, N, P per state per year ----
# Total sediment produced (kg/yr) = yield (kg/ha/yr) * Area_ha
df["Sed_total_kg_yr"] = df["Sediment_kg_ha_yr"] * df["Area_ha"]
df["N_total_kg_yr"]   = df["N_kg_ha_yr"]        * df["Area_ha"]
df["P_total_kg_yr"]   = df["P_kg_ha_yr"]        * df["Area_ha"]

# Nutrient content of sediment (mass fraction, not %); handle zero-division safely
df["N_frac"] = (df["N_kg_ha_yr"] / df["Sediment_kg_ha_yr"]).fillna(0).clip(lower=0)
df["P_frac"] = (df["P_kg_ha_yr"] / df["Sediment_kg_ha_yr"]).fillna(0).clip(lower=0)

# ---- 2) Gross nutrient value if ALL sediment is reused (no demand cap) ----
df["Gross_value_USD_yr"] = df["N_total_kg_yr"] * price_N + df["P_total_kg_yr"] * price_P

# ---- 3) Dose-specific coverage & demand-limited benefits ----
# For each dose, compute:
#  - Area covered by dose (ha) = Sed_total_kg_yr / dose
#  - Nutrient delivered per ha under dose (kg/ha) = dose * N_frac (or P_frac)
#  - Fraction of per-ha demand met: rN = N_per_ha / fert_N_need; rP = P_per_ha / fert_P_need
#  - Limiting fraction r* = min(rN, rP, 1.0)
#  - "Full-replacement equivalent hectares" = Area_covered * r*
#  - Demand-capped value = min(Gross_value, FullReplacementHa * (N_need*price_N + P_need*price_P))

for k, dose in doses.items():
    # area we can actually apply given the dose
    df[f"AreaCovered_{k}_ha"] = df["Sed_total_kg_yr"] / dose

    # per-ha nutrient delivery at this dose
    df[f"N_perha_{k}_kg"] = dose * df["N_frac"]
    df[f"P_perha_{k}_kg"] = dose * df["P_frac"]

    # fraction of agronomic demand met (cap at 1.0)
    df[f"rN_{k}"] = (df[f"N_perha_{k}_kg"] / fert_N_need).clip(upper=1.0)
    df[f"rP_{k}"] = (df[f"P_perha_{k}_kg"] / fert_P_need).clip(upper=1.0)

    # limiting nutrient determines full replacement equivalence
    df[f"rStar_{k}"] = df[[f"rN_{k}", f"rP_{k}"]].min(axis=1)

    # hectares that are fully replaced (nutrient-equivalent), bounded by area covered
    df[f"Ha_full_replaced_{k}"] = df[f"AreaCovered_{k}_ha"] * df[f"rStar_{k}"]

    # per-ha fertilizer value (if fully replaced both N & P)
    full_repl_value_per_ha = fert_N_need * price_N + fert_P_need * price_P

    # compute both options separately
    gross_value = df["Gross_value_USD_yr"]
    demand_limited_value = df[f"Ha_full_replaced_{k}"] * full_repl_value_per_ha

    # take the smaller (cannot exceed either)
    df[f"DemandCapped_value_{k}_USD_yr"] = pd.concat(
        [gross_value, demand_limited_value], axis=1
    ).min(axis=1)


# Save
df.to_csv("Output/Sediment_Econ_DemandLimited_byDose_State.csv", index=False)

# A compact view to inspect quickly
cols_show = ["State","Area_ha","Sediment_kg_ha_yr","N_kg_ha_yr","P_kg_ha_yr",
             "Sed_total_kg_yr","N_total_kg_yr","P_total_kg_yr","Gross_value_USD_yr"]
for k in doses.keys():
    cols_show += [f"AreaCovered_{k}_ha", f"Ha_full_replaced_{k}", f"DemandCapped_value_{k}_USD_yr"]
print(df[cols_show].round(2))

import matplotlib.pyplot as plt
import seaborn as sns

# Load the final data
df = pd.read_csv("Output/Sediment_Econ_DemandLimited_byDose_State.csv")

# For plotting aesthetics
sns.set(style="whitegrid", palette="Set2")

# Gather the columns for plotting
dose_labels = ["5t", "20t", "50t", "75t", "100t"]

# ---- Plot 1: Economic value per dose ----
plt.figure(figsize=(10,6))
value_cols = [f"DemandCapped_value_{d}_USD_yr" for d in dose_labels]
value_melt = df.melt(id_vars="State", value_vars=value_cols,
                     var_name="Dose", value_name="Value_USD_yr")

# Clean up labels
value_melt["Dose"] = value_melt["Dose"].str.extract("(\d+t)")

sns.barplot(data=value_melt, x="State", y="Value_USD_yr", hue="Dose")
plt.title("Annual Economic Value of Sediment Reuse by State and Application Dose")
plt.ylabel("Annual Economic Value (USD/year)")
plt.xlabel("State")
plt.legend(title="Application Dose")
plt.tight_layout()
plt.savefig("Output/Economic_Value_by_State_Dose.png", dpi=300)
plt.close()
print(" Saved figure: Economic_Value_by_State_Dose.png")

# ---- Plot 2: Fully replaced area (ha) per dose ----
plt.figure(figsize=(10,6))
area_cols = [f"Ha_full_replaced_{d}" for d in dose_labels]
area_melt = df.melt(id_vars="State", value_vars=area_cols,
                    var_name="Dose", value_name="Ha_full_replaced")

area_melt["Dose"] = area_melt["Dose"].str.extract("(\d+t)")

sns.barplot(data=area_melt, x="State", y="Ha_full_replaced", hue="Dose")
plt.title("Fully Fertilizer-Equivalent Area by State and Application Dose")
plt.ylabel("Equivalent Fully Replaced Area (ha)")
plt.xlabel("State")
plt.legend(title="Application Dose")
plt.tight_layout()
plt.savefig("Output/FullReplacedArea_by_State_Dose.png", dpi=300)
plt.close()
print(" Saved figure: FullReplacedArea_by_State_Dose.png")

