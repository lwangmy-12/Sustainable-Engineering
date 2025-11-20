# Project Report: Economic Potential of Sediment Reuse in the Great Lakes Region

**Author:** Mingyu Wang  
**Course:** Sustainable Engineering Principles  
**Date:** November 20, 2025  
**Version:** 3.0 (Draft Report Version)

---

## 1. Executive Summary
This project investigates the feasibility of recovering nutrient-rich sediment from stormwater runoff in the Great Lakes region for use as an agricultural fertilizer substitute. By analyzing USGS monitoring data, we estimated the recoverable mass of Particulate Nitrogen (N) and Phosphorus (P) and calculated their economic value based on commercial fertilizer prices.

**Key Findings:**
1.  **Regional Level**: The average economic potential across the entire region is low (**$5 - $25 per hectare**), primarily because high-quality sediment is diluted by large volumes of low-nutrient sediment from other areas.
2.  **Site-Specific Level**: A targeted analysis identified specific "hotspot" watersheds where sediment quality is significantly higher. The top sites yield sediment with an economic value exceeding **$300 per hectare**, making targeted extraction a viable sustainable engineering strategy.

---

## 2. Introduction
Nutrient pollution (N and P) in the Great Lakes poses a significant environmental challenge, leading to algal blooms and eutrophication. Simultaneously, agriculture relies heavily on commercial fertilizers. This project explores a circular economy solution: capturing sediment-bound nutrients from runoff and returning them to agricultural land.

The core objectives were:
1.  Quantify the mass of **recoverable nutrients** (specifically the particulate fraction) from USGS storm event data.
2.  Estimate the **economic value** of this sediment if used to replace Urea and DAP fertilizers.
3.  Determine whether this strategy is viable at a regional scale or requires a site-specific approach.

---

## 3. Methodology

### 3.1 Data Source
The analysis utilizes USGS storm event data (`All_EOF_StormEventLoadsRainCalculated.csv`), which includes:
-   **Runoff Volume**: Total water volume per storm event.
-   **Concentrations**: Raw concentrations (mg/L) of Total N, Total P, Orthophosphate, TKN, and Ammonia.

### 3.2 Nutrient Partitioning (The "Particulate" Logic)
A critical improvement in this analysis (v3.0) is the distinction between **dissolved** and **particulate** nutrients.
-   **Dissolved Nutrients** (e.g., Nitrate, Orthophosphate) stay in the water column and are lost during sediment dredging/dewatering.
-   **Particulate Nutrients** (Sediment-bound) are the only fraction recoverable for solid reuse.

We calculated the recoverable fraction as:
$$ P_{particulate} = P_{Total (unfiltered)} - P_{Orthophosphate (dissolved)} $$
$$ N_{particulate} = N_{TKN (unfiltered)} - N_{Ammonia+Ammonium (dissolved)} $$

### 3.3 Economic Valuation Models
We applied two distinct economic models to assess viability:

**Model A: Regional Fixed-Dose (General Assessment)**
-   **Assumption**: Sediment is applied at a standard rate of **20 tons/ha**.
-   **Calculation**: Value = (Recovered N/ha × Price N) + (Recovered P/ha × Price P).
-   **Purpose**: To see if "bulk" sediment reuse is economically attractive.

**Model B: Site-Specific P-Limited (Optimized Assessment)**
-   **Assumption**: Application rate is dynamic, limited by the crop's Phosphorus demand (to avoid P runoff).
-   **Calculation**: Dose = Crop P Demand / Sediment P Content.
-   **Purpose**: To find high-grade sites where the sediment is potent enough to be a valuable fertilizer.

---

## 4. Evolution of Analysis (v1 $\rightarrow$ v3)

The project underwent three phases of refinement to ensure accuracy:

| Version | Methodology | Limitation / Outcome |
| :--- | :--- | :--- |
| **v1.0** | **Yield-Based** (kg/ha) | Relied on watershed-normalized yields, which made calculating total recoverable mass difficult and inaccurate for reuse planning. |
| **v2.0** | **Concentration-Based** (Total N/P) | Solved the mass calculation issue but overestimated value by including dissolved nutrients that cannot be captured in sediment. |
| **v3.0** | **Particulate-Only** (Current) | **Most Accurate.** Isolates the sediment-bound fraction. This revealed that the "real" recoverable nutrient content is lower than Total N/P, necessitating a site-specific strategy. |

---

## 5. Results & Discussion

### 5.1 Regional Analysis Results
The regional aggregation (`Sediment_out.py` & `economic_value.py`) revealed that broad-scale sediment reuse is marginally economic.
-   **Sediment Grade**: The regional average sediment contains only **~0.5 - 1.0 g P/kg** and **~2 - 5 g N/kg**.
-   **Economic Return**: At a 20 t/ha application rate, the fertilizer savings are typically **$10 - $25 per hectare**.
-   **Conclusion**: Transporting and spreading 20 tons of soil to save $20 is likely not cost-effective given fuel and labor costs.

### 5.2 Site-Specific Optimization Results
Given the low regional average, we hypothesized that specific watersheds might produce "high-grade" sediment. The `Site_Specific_Analysis.py` script ranked sites by their potential value.

**Top Performing Sites (Hotspots):**
The analysis identified specific USGS stations where sediment quality is exceptional:

| Rank | USGS Station ID | Sediment Grade (N) | Sediment Grade (P) | Economic Value ($/ha) |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **435441087463900** | **3.22 g/kg** | **0.29 g/kg** | **$348.30** |
| **2** | 423954089071501 | 2.42 g/kg | 0.27 g/kg | $297.72 |
| **3** | 0408544209 | 2.66 g/kg | 0.21 g/kg | $289.72 |

**Interpretation**:
-   These sites produce sediment that is **10-15x more valuable** than the regional average.
-   The high value is driven by higher concentrations of particulate organic nitrogen.
-   **Strategic Implication**: Sediment recovery efforts should be **targeted** exclusively at these high-grade watersheds rather than implemented regionally.

---

## 6. Conclusion
This project demonstrates that while sediment reuse in the Great Lakes is not a "one-size-fits-all" solution, it holds significant potential as a targeted intervention.
1.  **Methodology Matters**: Distinguishing between dissolved and particulate nutrients was crucial for realistic economic estimation.
2.  **Selectivity is Key**: The economic viability hinges on site selection. Broad reuse is inefficient, but targeted recovery from hotspots (e.g., Station 435441087463900) can generate fertilizer savings exceeding **$300/ha**.
3.  **Future Work**: Further analysis should investigate the transport costs for these specific high-value sites to determine the net profit margin.

---

## Appendix: Project File Structure

### Core Scripts
1.  **`Sediment_out.py`**:
    -   *Role*: Data cleaning, particulate nutrient calculation, regional aggregation.
    -   *Output*: `Output/Annual_Region_Yields.csv`
2.  **`Sediment_Use.py`**:
    -   *Role*: Calculates reuse potential based on a fixed 20 t/ha dose.
    -   *Output*: `Output/Annual_Region_Reuse_Potential.csv`
3.  **`economic_value.py`**:
    -   *Role*: Regional economic valuation and trend plotting.
    -   *Output*: `Output/Annual_Region_Econ_Value.csv`, `Output/Econ_Trend_Plots/`
4.  **`Site_Specific_Analysis.py`**:
    -   *Role*: Identifies high-value hotspots using dynamic dosing logic.
    -   *Output*: `Output/Site_Specific_Economics.csv`, `Output/Top_Sites_Sediment_Grade.png`

### Key Output Files
-   `Output/Econ_Trend_Data.csv`: Summary of regional economic trends for plotting.
-   `Output/Top_Sites_Sediment_Grade.png`: Visualization of nutrient grades for the top 15 sites.
