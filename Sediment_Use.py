import pandas as pd
import os

folder = os.path.dirname(__file__)
os.chdir(folder)

# ============================================================
# 1. Load annual region-level yields (conc-based outputs)
# ============================================================
annual = pd.read_csv("Output/Annual_Region_Yields.csv")

# ============================================================
# 2. Dose assumption (20 t/ha = 20,000 kg/ha)
# ============================================================
DOSE_KG_PER_HA = 20000

# ============================================================
# 3. Compute reuse potential per year
#    ReuseArea_20t_ha = Total Sediment (kg) / 20,000 kg per ha
# ============================================================
annual["ReuseArea_20t_ha"] = annual["Total_Sediment_kg"] / DOSE_KG_PER_HA

# If no sediment → 0 ha
annual["ReuseArea_20t_ha"] = annual["ReuseArea_20t_ha"].fillna(0)

# ============================================================
# 4. Save output
# ============================================================
# 4. Save output（包含颗粒态N/P每公顷回收量）
out_path = "Output/Annual_Region_Reuse_Potential.csv"
# 只保留相关列，便于下游经济分析
cols_to_save = [
    "Year", "Total_Sediment_kg", "ReuseArea_20t_ha",
    "kgP_recovered_per_ha_20t", "kgN_recovered_per_ha_20t"
]
annual_out = annual[cols_to_save].copy()
annual_out.to_csv(out_path, index=False)

print(f"Created: {out_path}")
print(annual_out.head().round(2))
