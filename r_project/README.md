# CRADLE RStudio Spatial Analytics Replication Framework

This directory contains the independent **R / RStudio replication environment** for CRADLE (Critical Resource Allocation, Distribution & Location Engine).

It validates the spatial analytics, healthcare gap scores, desert detection, and candidate facility siting models in R using the spatial `sf` ecosystem, proving computational reproducibility across different software environments.

---

## 1. Project Structure

```text
r_project/
├── CRADLE_R.Rproj               # RStudio Project File (Double-click to open in RStudio)
├── README.md                    # This documentation file
├── data/                        # Independent GeoJSON and CSV datasets
│   ├── all_cities_wards.geojson
│   ├── all_cities_facilities.geojson
│   ├── processed_chennai_wards.geojson
│   ├── processed_coimbatore_wards.geojson
│   ├── processed_bengaluru_wards.geojson
│   └── processed_hyderabad_wards.geojson
├── scripts/                     # Modular R processing scripts
│   ├── 01_load_data.R           # Ingests GeoJSON boundaries & CSV facilities
│   ├── 02_preprocessing.R       # Spatial joins & distance calculations
│   ├── 03_gap_analyzer.R        # Computes 4-indicator Healthcare Gap Score
│   ├── 04_healthcare_deserts.R  # Detects urban healthcare deserts
│   ├── 05_candidate_scoring.R   # Ranks priority candidate facility sites
│   └── 06_validate_against_python.R # Numerical validation vs Python
└── outputs/                     # Generated validation metrics & tables
    └── r_python_validation_chennai.csv
```

---

## 2. Requirements & Package Installation

Open `CRADLE_R.Rproj` in RStudio. In the R console, execute:

```R
# Install required spatial and data manipulation packages
install.packages(c("sf", "readr", "dplyr", "ggplot2", "tidyr", "units", "lwgeom"))
```

---

## 3. How to Run

### Option A: Complete Pipeline Execution
Open `scripts/06_validate_against_python.R` and source it, or run:

```R
source("scripts/06_validate_against_python.R")
val_results <- run_validation("chennai")
print(val_results)
```

### Option B: Step-by-Step Execution
1. **Load Data:**
   ```R
   source("scripts/01_load_data.R")
   chn_data <- load_city_data("chennai")
   ```
2. **Spatial Integration & Preprocessing:**
   ```R
   source("scripts/02_preprocessing.R")
   preprocessed <- preprocess_city("chennai")
   ```
3. **Compute Healthcare Gap Scores:**
   ```R
   source("scripts/03_gap_analyzer.R")
   wards_gap <- calculate_gap_scores_r(preprocessed$wards)
   ```
4. **Detect Healthcare Deserts:**
   ```R
   source("scripts/04_healthcare_deserts.R")
   wards_deserts <- detect_healthcare_deserts_r(wards_gap)
   ```
5. **Score Candidate Sites:**
   ```R
   source("scripts/05_candidate_scoring.R")
   candidates <- rank_candidates_r(wards_deserts, preprocessed$facilities)
   ```

---

## 4. Multi-City Support in R

The functions accept `city_key`:
- `"chennai"` (Metric CRS: `EPSG:32644`)
- `"coimbatore"` (Metric CRS: `EPSG:32643`)
- `"bengaluru"` (Metric CRS: `EPSG:32643`)
- `"hyderabad"` (Metric CRS: `EPSG:32644`)
- `"delhi"` (Metric CRS: `EPSG:32643`)

Example:
```R
val_del <- run_validation("delhi")
val_blr <- run_validation("bengaluru")
val_hyd <- run_validation("hyderabad")
```

---

## 5. Numerical Parity Summary

| Analytical Indicator | Formula Definition | Pearson $r$ | Concordance | Tolerance | Status |
|---|---|---|---|---|---|
| **Healthcare Gap Score** | $0.30 \times Pop + 0.30 \times Cap + 0.25 \times Dist + 0.15 \times Scarcity$ | **1.000000** | MAE: 0.0000 | $< 10^{-4}$ | **PASS** |
| **Priority Classification** | Critical $\ge 70$, High $\ge 50$, Mod $\ge 25$, Low $< 25$ | - | **100.0%** | Exact match | **PASS** |
| **Desert Detection** | Multi-criteria spatial and bed deficit threshold | - | **100.0%** | Exact match | **PASS** |
