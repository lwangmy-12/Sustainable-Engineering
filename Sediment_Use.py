import pandas as pd
import os

folder = os.path.dirname(__file__)
os.chdir(folder)

# read previous outpur
state_yield = pd.read_csv("Output/State_Average_Annual_Yields.csv")
site_table = pd.read_csv("RAW/EOF_Site_Table.csv", encoding="latin1")

# units
site_table["Area_ha"] = site_table["Area"] * 0.4047

# per state
state_area = site_table.groupby("State")["Area_ha"].sum().reset_index()

# murged yields and area
merged = state_yield.merge(state_area, on="State", how="left")

# assumed (kg/ha)
doses = [20000, 50000, 75000, 100000]
for d in doses:
    merged[f"ReuseArea_{int(d/1000)}t_ha"] = (merged["Sediment_kg_ha_yr"] * merged["Area_ha"]) / d

# output
merged.to_csv("Output/Sediment_Reuse_Potential_by_State.csv", index=False)
print(merged)
