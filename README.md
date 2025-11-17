# README – Sediment Reuse Economic Potential Analysis (Great Lakes Region)
**Author:** Mingyu Wang  
**Project:** Sustainable Engineering Principles – Nutrient-Rich Sediment Reuse  
**Date:** November 2025  

---

## 1. Objective
This analysis estimates how much **agricultural sediment collected from edge-of-field (EOF) monitoring sites** in the Great Lakes states (Ohio, Indiana, Michigan, Wisconsin, and New York) could be reused as a source of nitrogen (N) and phosphorus (P) fertilizer.

The goal is to determine:
- Annual sediment, N, and P generated from USGS EOF sites  
- How much cropland that sediment could fertilize under different application doses  
- The potential fertilizer cost savings if nutrients replaced synthetic fertilizers  
- Basic interpretation of economic and environmental significance

---

## 2. Data Sources

### 2.1 USGS Edge-of-Field (EOF) Monitoring Data
Data come from the **USGS Edge-of-Field Monitoring Program**, which measures sediment and nutrient losses from agricultural runoff.

**Files used:**
- `EOF_Site_Table.csv` – Metadata for each monitoring site (state, area, ID, site type)
- `All_EOF_StormEventLoadsRainCalculated.csv` – Per-event sediment, nitrogen, and phosphorus loads

**Unit conversion:**  
1 pound per acre = 1.12085 kilograms per hectare

---

### 2.2 Reference Fertilizer Values
To estimate fertilizer replacement:
- Typical fertilizer requirement (for corn): 150 kg N/ha and 22 kg P/ha per year  
- Average fertilizer market price: 1.89 USD/kg N, 5.37 USD/kg P  

Sources: USDA ERS Fertilizer Use and Price dataset and market averages (2024–2025).

---

## 3. File Overview

| File | Function |
|------|-----------|
| `Sediment_out.py` | Extracts USGS data, aggregates annual sediment/N/P yields per site and per state |
| `Sediment_Use.py` | Combines yields with monitored area to estimate how much land could be fertilized at various doses |
| `economic_value.py` | Calculates nutrient and economic value for each dose (5, 20, 50, 75, 100 t/ha), and produces comparison plots |

---

## 4. Methods

### Step 1 – Data Extraction and Conversion (`Sediment_out.py`)
1. Select monitoring sites in the five Great Lakes states.  
2. Aggregate all storm-event sediment, N, and P loads per year and per site.  
3. Convert units from pounds per acre to kilograms per hectare.  
4. Calculate average annual sediment and nutrient yield for each state.  
5. Export:
   - `Annual_Sediment_Nutrient_Loads.csv`
   - `State_Average_Annual_Yields.csv`
   - Trend plots for sediment, N, and P

---

### Step 2 – Sediment Reuse Potential (`Sediment_Use.py`)
1. Convert site drainage areas from acres to hectares.  
2. Calculate total monitored area per state.  
3. Merge with state-average yields of sediment, N, and P.  
4. Estimate total sediment produced and how much land could be covered at doses of 20, 50, 75, and 100 tonnes per hectare.  
   - For example, 20 t/ha means every hectare receives 20,000 kg of sediment.  
   - The total area covered equals total sediment divided by the dose.  
5. Export results as `Sediment_Reuse_Potential_by_State.csv`.

---

### Step 3 – Economic Valuation (`economic_value.py`)
1. **Total production** – Multiply average yield by total monitored area to get total sediment, N, and P mass per year for each state.  
2. **Nutrient composition** – Calculate how much nitrogen and phosphorus are contained in each kilogram of sediment.  
3. **Gross nutrient value** – Multiply total N and P by their market prices. This gives the theoretical maximum fertilizer value if all nutrients were fully used.  
4. **Demand-capped adjustment** – Compare nutrients applied at each dose with crop nutrient needs.  
   - If applied nutrients exceed crop demand, they are capped at 100%.  
   - If nutrients are below demand, only that fraction counts as fertilizer replacement.  
   - The smaller of N or P determines the “bottleneck” ratio (r*).  
5. **Fully replaced area** – Multiply the coverage area by the bottleneck ratio to find the area where both N and P needs are met.  
6. **Economic value per dose** – Multiply that area by per-hectare fertilizer cost. The smaller of this or the gross value is recorded as the final “demand-capped” value.  
7. **Visualization** – Create bar charts of total annual economic value and fully replaced area by state and dose.

---

## 4.1 **NEW (v2.0)** – Calculation Basis & Recovery Parameters

**Critical improvements in v2.0:**

The previous version (v1.0) contained a **fundamental conceptual error** in economic calculations. This has been corrected in v2.0:

| Aspect | v1.0 (Incorrect) | v2.0 (Correct) |
|--------|------------------|-----------------|
| **Nutrient basis** | Used `N_kg_ha_yr` from monitoring area as applied-per-ha nutrient | Uses `Total_N_kg ÷ ReuseArea_20t_ha` (correct per-ha when applied to farmland) |
| **Calculation error** | Mixed monitoring-watershed basis (Effective_Area_ha) with reuse-area basis → **10-100x underestimate or overestimate** | Consistent basis throughout: all nutrients calculated per hectare of actual reuse area |
| **Recovery efficiency** | Assumed 100% nutrient availability | Accounts for 80% recovery efficiency after processing |
| **N availability** | Assumed instant availability | 50% available in-season (organic N requires mineralization time) |
| **P availability** | Assumed instant availability | 80% available (P solubility/fixation losses) |
| **Economic method** | Single limiting-nutrient approach only | **Two methods provided**: (A) limiting-nutrient, (B) separate N/P pricing for transparency |
| **Division by zero** | No protection when ReuseArea = 0 → produces `inf` values | Protected with `.replace(0, np.nan)` |
| **Year filtering** | Used all annual data regardless of QC validity | Fixed: uses only `annual_valid` (passes quality checks) |
| **Output years** | Only 2 years appearing in outputs | All 22 years (2002–2023) now correctly appear |

**Example of v1.0 vs v2.0 error magnitude (Year 2005):**
- **v1.0 logic**: N_kg_ha_yr (0.165 kg/ha on 942 ha monitoring area) × ReuseArea (3.99 ha) = Wrong mixing of bases  
- **v2.0 logic**: Total_N_kg (155.9 kg) ÷ ReuseArea (3.99 ha) = **39.09 kg/ha applied** ← 236× larger, physically realistic for 20 t/ha sediment dose

**Impact on economic results:**
- v1.0 typically underestimated economic value by **50–200%** due to incorrect basis
- v2.0 provides physically defensible estimates accounting for nutrient cycling losses

---

## 5. Outputs

| Output File | Description |
|--------------|-------------|
| `Annual_Sediment_Nutrient_Loads.csv` | Annual sediment, N, and P loads per site and year |
| `State_Average_Annual_Yields.csv` | Average annual sediment/N/P yields per state |
| `Sediment_Reuse_Potential_by_State.csv` | Estimated total sediment/N/P production and coverage area per dose |
| `Sediment_Econ_DemandLimited_byDose_State.csv` | Final demand-capped economic value per state and dose |
| `Economic_Value_by_State_Dose.png` | Bar chart of annual economic values |
| `FullReplacedArea_by_State_Dose.png` | Bar chart of fully fertilizer-equivalent area |

---

## 6. Results and Interpretation

- **Wisconsin (WI)** has the largest monitored area and sediment yield.  
  - Gross fertilizer-equivalent value ≈ 45,943 USD/year  
  - Demand-capped value (20 t/ha) ≈ 25,497 USD/year  
  - Fully replaced area ≈ 63.5 ha (about 5% of monitored drainage area)  

- **Other states (IN, MI, NY, OH)** have small monitored areas and minimal economic potential (hundreds of dollars per year).  

- **Dose comparison:**  
  - At lower doses (e.g., 5 t/ha), more area can be covered, but nutrient sufficiency per hectare is lower.  
  - At higher doses (50–100 t/ha), each hectare receives enough nutrients, but the total covered area decreases.  
  - For WI, the best tradeoff occurs around 5–10 t/ha; at higher doses, total economic value decreases.

---

## 7. Current Limitations and Uncertainties

| Issue | Explanation |
|--------|-------------|
| **Economic valuation** | Current analysis only estimates the *potential* value of recovered nutrients. It does not include excavation, dewatering, hauling, or land application costs. Net savings have not yet been calculated. |
| **Drainage vs. cropland area** | The monitored “drainage area” represents the hydrologic catchment that contributes runoff, not necessarily the farmland where sediment could be reused. Thus, results represent only the monitored network, not all agricultural land in each state. |
| **Fertilizer needs and prices** | Fixed average values are used for simplicity (150 kg N/ha, 22 kg P/ha). Actual crop needs vary with soil type, crop species, and management practices. |
| **Environmental benefits** | The analysis does not yet include environmental benefits such as reduced eutrophication, avoided dredging, or avoided GHG emissions from fertilizer manufacturing. |
| **Scaling to statewide values** | State-level estimates require including cropland area data from USDA NASS to relate monitored areas to total agricultural land. |
| **Nutrient bioavailability** | Assumes all sediment nutrients are available for crops, which may overestimate real benefits. Laboratory nutrient release data are needed for refinement. |

---

## 8. Future Work

1. **Net Economic Benefit**  
   Add cost components for excavation, dewatering, transport, and field application to calculate net savings: fertilizer cost avoided minus reuse cost, plus avoided disposal cost.  

2. **Environmental Benefit Quantification**  
   Estimate avoided phosphorus loads and monetize them using published “cost per kilogram of P removed” from water bodies.  

3. **Spatial Scaling**  
   Use USDA NASS cropland data to extrapolate from monitored areas to total cropland in each state.  

4. **Sensitivity Analysis**  
   Evaluate how fertilizer prices, nutrient content, and cost parameters influence results and identify key uncertainties.  

5. **Integrated Economic–Environmental Evaluation**  
   Combine economic and environmental metrics into a unified benefit index for policy-level assessment.

---

## 9. Summary

This workflow connects hydrologic monitoring data with fertilizer economics to assess the **potential value of nutrient-rich sediment reuse**.

Key points:
- The monitored EOF areas represent a small but measurable resource for nutrient recovery.  
- Wisconsin shows the highest localized potential (~25,000 USD/year under demand-capped assumptions).  
- However, the results reflect *potential value*, not net savings, as no cost data are included yet.  
- Future work should link monitored catchments to real cropland, integrate cost data, and add environmental impact assessment.

---
