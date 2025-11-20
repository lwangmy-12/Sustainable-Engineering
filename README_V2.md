# README – Sediment Reuse Economic Potential Analysis (Great Lakes Region)
**Author:** Mingyu Wang  
**Project:** Sustainable Engineering Principles – Nutrient-Rich Sediment Reuse  
**Date:** November 2025  
**Version:** 2.0

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
- `All_EOF_StormEventLoadsRainCalculated.csv` – Per-event sediment, nitrogen, and phosphorus loads using **concentration-based calculation** (v2.0)

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

| File | Function | v2.0 Update |
|------|-----------|-------------|
| `Sediment_out.py` | Extracts USGS data using **concentration-based calculation**, aggregates annual sediment/N/P totals | **Changed from yield-based to concentration-based**; fixed year filtering to use only QC-valid data |
| `Sediment_Use.py` | Combines aggregated masses with monitored area to estimate how much land could be fertilized at 20 t/ha dose | No major changes |
| `economic_value.py` | Calculates nutrient recovery and economic value per hectare of reuse area, accounting for recovery/availability losses | **MAJOR REFACTOR** – fixed basis mixing error, added recovery/availability params, two economic methods |

---

## 4. Methods

### Step 1 – Data Extraction and Conversion (`Sediment_out.py`)
1. Select monitoring sites in the five Great Lakes states.  
2. **v2.0 METHOD (Concentration-based):** For each storm event, compute nutrient and sediment masses from:
   - `mass (kg) = concentration (mg/L) × runoff_volume (L) ÷ 1e6`
   - Uses columns: `total_phosphorus_unfiltered_conc_mgL`, `total_nitrogen_conc_mgL`, `suspended_sediment_conc_mgL`, `runoff_volume`
   - *This replaces v1.0's deprecated yield-based approach*
3. Aggregate all storm-event sediment, N, and P **masses** per year and per site.  
4. Convert units from pounds to kilograms (where applicable).  
5. Calculate average annual sediment and nutrient **yields** (total mass ÷ site area) for each station-year.  
6. **v2.0 fix:** Only use events/years that pass quality control checks (`Valid` flag).
7. Export:
   - `Annual_Region_Yields.csv` (regional aggregates, all 22 years)
   - Trend plots for sediment, N, and P

---

### Step 2 – Sediment Reuse Potential (`Sediment_Use.py`)
1. Convert site drainage areas from acres to hectares.  
2. Calculate total monitored area per state.  
3. Merge with state-average yields of sediment, N, and P.  
4. Estimate total sediment produced and how much land could be covered at a dose of 20 tonnes per hectare.  
   - For example, 20 t/ha means every hectare receives 20,000 kg of sediment.  
   - The total area covered equals total sediment divided by the dose.  
5. Export results as `Annual_Region_Reuse_Potential.csv`.

---

### Step 3 – Economic Valuation (`economic_value.py`) — **UPDATED in v2.0**

**v2.0 Method (Corrected Basis & Recovery Factors):**

1. **Applied per-hectare N and P** – This is the KEY FIX in v2.0:
   - `N_applied_kg_per_ha = Total_N_kg ÷ ReuseArea_20t_ha`  
   - `P_applied_kg_per_ha = Total_P_kg ÷ ReuseArea_20t_ha`  
   - *(Correct basis: nutrients per hectare of farmland receiving sediment, not monitoring basis)*

2. **Account for recovery and availability losses** – Added in v2.0 for physical realism:
   - Recovery efficiency: 80% (processing/handling losses)
   - N availability: 50% (organic N requires mineralization; not all available in-season)
   - P availability: 80% (some P fixed in soil; some loss to groundwater)
   - `N_usable_kg_per_ha = N_applied_kg_per_ha × 0.80 × 0.50`
   - `P_usable_kg_per_ha = P_applied_kg_per_ha × 0.80 × 0.80`

3. **Nutrient replacement ratio** – Compare usable nutrients to typical crop demand:
   - `Percent_saved_N = min(N_usable_kg_per_ha ÷ 150, 1.0)` 
   - `Percent_saved_P = min(P_usable_kg_per_ha ÷ 22, 1.0)`  
   - Limiting nutrient = min(N, P) ratio

4. **Economic value – Two methods for transparency:**
   - **Method A (Limiting-nutrient):** Only the limiting nutrient is valued
     - `Cost_reduction_total_USD_limiting = Percent_saved_total × cost_per_ha × ReuseArea_20t_ha`
   - **Method B (By-price, recommended):** Separately value each nutrient by market price
     - `N_saving_USD_per_ha = N_usable_kg_per_ha × $1.89/kg` (capped at 150 kg/ha demand)
     - `P_saving_USD_per_ha = P_usable_kg_per_ha × $5.37/kg` (capped at 22 kg/ha demand)
     - `Cost_reduction_total_USD = (N_saving + P_saving) × ReuseArea_20t_ha`
     - *This method avoids double-counting and better represents economic value when N and P are priced differently*

5. **Visualization:**
   - Comparison plots showing both economic methods (v2.0)
   - Applied N/P per hectare vs. crop demand (new in v2.0)
   - Per-hectare and total annual economic value trends

---

## 4.1 **Version Comparison: v1.0 vs v2.0**

**Critical improvements in v2.0:**

The previous version (v1.0) had two major issues:

### Issue 1: Data Calculation Method – Yield vs. Concentration

**v1.0 Approach (Deprecated – Yield-Based):**
```python
# v1.0 code used pre-calculated yield columns:
load_cols = [
    "USGS_Station_Number",
    "Year",
    "suspended_sediment_yield_pounds_per_acre",
    "total_nitrogen_yield_pounds_per_acre",
    "total_phosphorus_unfiltered_yield_pounds_per_acre"
]
# Simply summed yields across sites
```
**Problems:**
- Yields are **intensive properties** (per-unit-area values specific to each site's drainage area)
- Summing yields across multiple sites with different areas is **incorrect** (mixes different reference areas)
- Cannot properly account for varying runoff volumes across different storm events
- Less transparent; hides the physical basis of calculations

**v2.0 Approach (Correct – Concentration-Based):**
```python
# v2.0 code uses concentration columns:
P_conc = "total_phosphorus_unfiltered_conc_mgL"
N_conc = "total_nitrogen_conc_mgL"
sed_conc = "suspended_sediment_conc_mgL"

# Compute mass per event: mass (kg) = concentration (mg/L) × runoff volume (L) ÷ 1e6
events["P_mass_kg"] = (events[P_conc] * events["runoff_volume"]) / 1e6
events["N_mass_kg"] = (events[N_conc] * events["runoff_volume"]) / 1e6

# Aggregate masses, then compute yields
annual = df.groupby(["USGS_Station_Number","Year"], as_index=False).agg({
    "P_mass_kg": "sum",
    "N_mass_kg": "sum",
    "Area_ha": "first"
})
```
**Advantages:**
- **Physically correct:** Concentration × volume → mass is the proper hydrologic calculation
- **Maintains water balance:** Each event's unique runoff volume is accounted for
- **Proper aggregation:** Masses are **extensive properties** (can be summed across sites)
- **Regulatory quality:** Suitable for peer review and publication
- **Transparent:** Clear linkage between concentration, runoff, and mass

**Example difference (Year 2005):**
- **v1.0:** Pre-calculated yield values summed directly (conceptually flawed when aggregating multiple sites)
- **v2.0:** 
  - Event 1: 15 mg/L × 5,000 L ÷ 1e6 = 0.075 kg N
  - Event 2: 22 mg/L × 8,000 L ÷ 1e6 = 0.176 kg N
  - Year total: 0.075 + 0.176 + ... = 155.9 kg N ✓ (correct)

---

### Issue 2: Economic Calculation Basis – Monitoring Area vs. Reuse Area

**v1.0 also contained a fundamental conceptual error** in economic calculations. This has been corrected in v2.0:

| Aspect | v1.0 (Incorrect) | v2.0 (Corrected) |
|--------|------------------|-----------------|
| **Data source** | Pre-calculated yield columns from raw data | Concentration (mg/L) × runoff volume (L) → mass (kg) |
| **Calculation basis** | Yield-based (intensive property) | Mass-based (extensive property) |
| **Aggregation method** | Sum yields across sites (incorrect) | Sum masses across sites, compute yields (correct) |
| **Runoff accounting** | Not transparent; hides runoff volume variations | Explicit: each event's runoff volume used |
| **Nutrient per-hectare basis** | Used `N_kg_ha_yr` from monitoring area as applied-per-ha nutrient | Uses `Total_N_kg ÷ ReuseArea_20t_ha` (correct per-ha on farmland) |
| **Basis mixing error** | Mixed monitoring-watershed basis (Effective_Area_ha) with reuse-area basis → **10-100x error** | Consistent basis: all nutrients calculated per hectare of actual reuse area |
| **Recovery efficiency** | Assumed 100% nutrient availability | Accounts for 80% recovery efficiency after processing |
| **N availability** | Assumed instant availability | 50% available in-season (organic N requires mineralization) |
| **P availability** | Assumed instant availability | 80% available (P solubility/fixation losses) |
| **Economic methods** | Single limiting-nutrient approach only | **Two methods**: (A) limiting-nutrient, (B) separate N/P pricing |
| **Division by zero** | No protection when ReuseArea = 0 → `inf` values | Protected with `.replace(0, np.nan)` |
| **Year filtering** | Used all annual data regardless of QC validity | Uses only `annual_valid` (passes quality checks) |
| **Output years** | Only 2 years appearing (bug) | All 22 years (2002–2023) correctly appear |

**Concrete example of v1.0 vs v2.0 errors (Year 2005):**

**Error 1 – Data calculation method:**
- **v1.0:** 
  - Summed pre-calculated `total_nitrogen_yield_pounds_per_acre` directly from raw data
  - Did not account for different runoff volumes across events
  - Conceptually wrong when aggregating multiple sites with different drainage areas

- **v2.0:**
  - Event 1: 15 mg/L N × 5,000 L runoff ÷ 1e6 = 0.075 kg N
  - Event 2: 22 mg/L N × 8,000 L runoff ÷ 1e6 = 0.176 kg N
  - Year total: 0.075 + 0.176 + ... = 155.9 kg N ✓ (physically correct, water balance maintained)

**Error 2 – Economic basis mixing:**
- **v1.0 calculation:**  
  - `N_kg_ha_yr` = 0.165 kg/ha (computed on 942 ha monitoring area)  
  - Incorrectly used this as applied-per-ha nutrient for farmland  
  - Mixed monitoring basis with reuse basis = **nonsensical**
  
- **v2.0 calculation:**  
  - `Total_N_kg` = 155.9 kg (from proper mass-based aggregation)
  - `N_applied_kg_per_ha` = 155.9 kg ÷ 3.99 ha reuse area = **39.09 kg/ha**  
  - This is **236× larger** than v1.0's approach and physically realistic for 20 t/ha sediment dose

**Impact on economic results:**
- v1.0: Year 2005 cost reduction ≈ $40 USD (underestimated)
- v2.0 (by-price method): Year 2005 cost reduction ≈ $215 USD (correct, accounts for N and P separately)
- v1.0 typically **underestimated economic value by 50–200%** overall
- v2.0 provides **physically defensible estimates** accounting for organic matter processing losses and nutrient cycling

---

## 5. Outputs

| Output File | Description |
|--------------|-------------|
| `Annual_Region_Yields.csv` | Annual sediment, N, and P aggregated by year (regional totals); includes per-hectare yields based on monitoring area |
| `Annual_Region_Reuse_Potential.csv` | Regional totals with added `ReuseArea_20t_ha` column showing how many hectares of farmland can receive sediment at 20 t/ha dose |
| `Annual_Region_Econ_Value.csv` | Economic valuations by year using both Methods A & B; includes columns for applied N/P, usable N/P (after recovery), and cost reduction estimates |
| `Sediment_Total_Trend.png` | Plot of total sediment (kg) by year from monitoring |
| `Sediment_Yield_Trend.png` | Plot of sediment yield (kg/ha on monitoring area) by year |
| `N_Total_Trend.png` | Plot of total N (kg) by year from monitoring |
| `N_Yield_Trend.png` | Plot of N yield (kg/ha on monitoring area) by year |
| `P_Total_Trend.png` | Plot of total P (kg) by year from monitoring |
| `P_Yield_Trend.png` | Plot of P yield (kg/ha on monitoring area) by year |
| `Econ_Trend_Plots/` | Folder containing v2.0 plots: `Cost_Reduction_Trend.png` (both methods), `Cost_Reduction_per_ha.png`, `Applied_NP_Trend.png` (new in v2.0) |

---

## 6. Results and Interpretation (v2.0)

**Key findings from corrected calculations:**

- **Reuse area (20 t/ha):** Varies from 0.2 to 16.4 hectares per year (2002–2023 average: ~6.8 ha)
- **Applied N per hectare:** Ranges from 4.6 to 67.2 kg/ha (highly variable; depends on sediment quantity and reuse area)
- **Applied P per hectare:** Ranges from 0.6 to 3.4 kg/ha (generally well below 22 kg/ha crop demand)
- **Limiting nutrient:** Phosphorus (P) is almost always limiting; N replacement typically 3-18% of crop demand
- **Annual economic value (by-price method):** Ranges from ~$4 to ~$366 USD/year
  - Years with more sediment AND smaller reuse area = higher per-hectare nutrient content = higher value
  - Years with large reuse area but modest total sediment = dilute nutrient content = lower per-hectare value

**Limiting nutrient effect:**
- Sediment can supply only partial crop P requirements (typically 10–35% of 22 kg/ha demand)
- N is usually less limiting (40–200% of demand depending on year)
- Economic value is primarily determined by P replacement potential

---

## 7. Current Limitations and Uncertainties

| Issue | Explanation |
|--------|-------------|
| **Economic valuation – scope** | Current analysis estimates the *potential* fertilizer cost avoided. It does **NOT** include excavation, dewatering, hauling, processing, or land application costs. Net savings have not yet been calculated. |
| **Drainage vs. cropland area** | The monitored "drainage area" represents the hydrologic catchment contributing runoff, not necessarily the farmland where sediment could be reused. Results reflect only the EOF monitoring network, not all agricultural land in Great Lakes region. |
| **Recovery and availability parameters** | Recovery efficiency (80%), N availability (50%), and P availability (80%) are assumed constant. These vary by: sediment type, handling method, climate, soil type, and farming practice. Site-specific values would improve estimates. |
| **Fertilizer needs and prices** | Fixed average values used (150 kg N/ha, 22 kg P/ha, $1.89/kg N, $5.37/kg P). Actual crop needs vary with soil type, crop species, and management practices; prices fluctuate seasonally. |
| **Environmental benefits** | The analysis does not include environmental co-benefits such as reduced eutrophication, avoided dredging, or avoided GHG emissions from synthetic fertilizer manufacturing. |
| **Scaling to statewide values** | Regional estimates do not extrapolate to all agricultural land; would require USDA NASS cropland area data to relate monitored areas to total state/regional potential. |

---

## 8. Future Work

1. **Net Economic Benefit**  
   Add cost components (excavation, processing, transport, land application) to calculate **net savings** = fertilizer cost avoided minus reuse cost, plus avoided disposal cost.  

2. **Environmental Benefit Quantification**  
   Estimate avoided phosphorus loads and monetize using published "cost per kilogram of P removed" values from water quality studies.  

3. **Spatial Scaling**  
   Use USDA NASS cropland data to extrapolate from monitored EOF network to total cropland in each state/region.  

4. **Sensitivity and Uncertainty Analysis**  
   Evaluate how fertilizer prices, recovery efficiency, N/P availability, and cost parameters influence results. Identify key uncertainties.  

5. **Bioavailability Testing**  
   Conduct laboratory nutrient release studies to refine recovery and availability assumptions beyond current constant-fraction approach.

6. **Site-Specific vs. Regional Approach**  
   Develop methodology to apply site-specific recovery/availability parameters based on sediment composition and processing method.

---

## 9. Summary

This workflow connects hydrologic monitoring data with fertilizer economics to assess the **potential value of nutrient-rich sediment reuse** using physically realistic calculations.

**Key points:**
- The monitored EOF network represents a small but measurable regional resource for nutrient recovery (~6.8 ha reuse area per year at 20 t/ha dose).
- **v2.0 correction:** Switched from incorrect mixing of monitoring and reuse bases to consistent per-hectare calculation on actual farmland.
- Annual economic value (by-price method, 20 t/ha) ranges from ~$4 to ~$366 USD, with average ~$100 USD/year.
- Phosphorus is almost always the limiting nutrient due to low sediment P content relative to crop demand.
- Results reflect **potential value**, not net savings, as no cost data are included yet.
- Future work should include reuse costs, environmental benefit valuation, and spatial scaling to regional agricultural context.

---

**v2.0 Release Notes:**
- Fixed year filtering bug (now 22 years instead of 2)
- Corrected nutrient basis calculation (per-hectare reuse area, not monitoring area)
- Added recovery efficiency and nutrient availability parameters
- Implemented two economic valuation methods for transparency
- Added numpy import and division-by-zero protection
- New visualization: Applied N/P vs. crop demand

