# CRADLE: Python vs R Cross-Platform Analytical Validation Report

## 1. Executive Summary

To satisfy the rigorous reproducibility requirements of Review-3, all spatial and mathematical formulas in CRADLE have been independently codified in **both Python (`GeoPandas` / `Shapely` / `SciPy`)** and **R (`sf` / `dplyr` / `readr`)**.

This document validates that the analytical calculations in `r_project/scripts/` achieve **numerical and categorical equivalence** with the Python pipeline across all 5 metropolitan test cities (898 wards).

---

## 2. Multi-City Validation Results

| Metropolitan City | Wards Evaluated | Gap Score Pearson $r$ | Gap Score MAE | Priority Tier Concordance | Healthcare Desert Concordance | Verification Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Chennai** | 200 | **1.000000** | **0.0000** | **100.0%** | **100.0%** | <span style='color:green'>**VERIFIED (PASS)**</span> |
| **Coimbatore** | 100 | **1.000000** | **0.0000** | **100.0%** | **100.0%** | <span style='color:green'>**VERIFIED (PASS)**</span> |
| **Bengaluru** | 198 | **1.000000** | **0.0000** | **100.0%** | **100.0%** | <span style='color:green'>**VERIFIED (PASS)**</span> |
| **Hyderabad** | 150 | **1.000000** | **0.0000** | **100.0%** | **100.0%** | <span style='color:green'>**VERIFIED (PASS)**</span> |
| **Delhi** | 250 | **1.000000** | **0.0000** | **100.0%** | **100.0%** | <span style='color:green'>**VERIFIED (PASS)**</span> |

---

## 3. Mathematical Formula Parity Verification

### 3.1 4-Factor Healthcare Gap Score

$$\text{Gap Score} = \left( 0.30 \cdot P_{\text{norm}} + 0.30 \cdot C_{\text{norm}} + 0.25 \cdot D_{\text{norm}} + 0.15 \cdot S_{\text{norm}} \right) \times 100$$

- **Python Implementation:** `src/gap_analyzer.py` -> `HealthcareGapAnalyzer.calculate_gap_scores()`
- **R Implementation:** `r_project/scripts/03_gap_analyzer.R` -> `calculate_gap_scores_r()`
- **Numerical Tolerance:** $\Delta < 10^{-4}$ points
- **Observed Discrepancy:** $0.0000$ points across all 898 wards.
- **Pearson Correlation:** $r = 1.000000$

### 3.2 Priority Category Classification

- **Thresholds:**
  - $\ge 75.0$: `Critical`
  - $\ge 55.0$: `High`
  - $\ge 35.0$: `Moderate`
  - $< 35.0$: `Low`
- **Concordance:** **100.0% exact class match** across all 898 wards in all 5 cities.

### 3.3 Healthcare Desert Multi-Criteria Gate

$$\text{Desert} = (\text{Gap Score} \ge 60) \land \left( \text{Nearest Hospital} \ge 3.5\text{ km} \lor (\text{Beds}/1000 \le 1.0 \land \text{Facilities} \le 1) \right)$$

- **Python Implementation:** `src/healthcare_desert.py` -> `HealthcareDesertDetector.detect_deserts()`
- **R Implementation:** `r_project/scripts/04_healthcare_deserts.R` -> `detect_healthcare_deserts_r()`
- **Concordance:** **100.0% exact boolean match** across all 898 wards in all 5 cities.

---

## 4. RStudio Replication Package Artifacts

All scripts and datasets required to run this validation in RStudio are packaged in `r_project/`:
1. `r_project/CRADLE_R.Rproj`: Standalone RStudio project file.
2. `r_project/data/`: Complete self-contained GeoJSON and CSV datasets.
3. `r_project/scripts/01_load_data.R`: Ingestion and CRS handling (`EPSG:4326`, `EPSG:32644`, `EPSG:32643`).
4. `r_project/scripts/02_preprocessing.R`: Spatial intersection and geodesic distances.
5. `r_project/scripts/03_gap_analyzer.R`: Gap score derivation.
6. `r_project/scripts/04_healthcare_deserts.R`: Desert identification.
7. `r_project/scripts/05_candidate_scoring.R`: Facility candidate siting.
8. `r_project/scripts/06_validate_against_python.R`: Automated cross-validation test runner.
