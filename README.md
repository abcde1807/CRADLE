# CRADLE: Critical Resource Allocation, Distribution & Location Engine
### Multi-City Urban Healthcare Spatial Decision-Support & Machine Learning System
#### Tamil Nadu (Chennai, Coimbatore), Karnataka (Bengaluru), Telangana (Hyderabad), Delhi (NCT), India

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![GeoPandas](https://img.shields.io/badge/GIS-GeoPandas%20%7C%20Shapely-green.svg)](https://geopandas.org/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn%20(LOCO%20CV)-blueviolet.svg)](https://scikit-learn.org/)
[![R Replication](https://img.shields.io/badge/RStudio-sf%20%7C%20dplyr-steelblue.svg)](https://www.r-project.org/)
[![Optimization](https://img.shields.io/badge/Optimization-PuLP%20(MCLP)-orange.svg)](https://coin-or.github.io/pulp/)
[![Dashboard](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)]()

---

## 1. Project Overview

**CRADLE (Critical Resource Allocation, Distribution & Location Engine)** is an enterprise-grade urban healthcare spatial decision-support system designed to optimize healthcare facility siting across Indian metropolitan regions.

Traditional healthcare infrastructure siting tools ask:
> *"Where is vacant land suitable for a hospital?"*

**CRADLE inverts this paradigm through a Gap-First Spatial Allocation Framework:**
> *"Where is healthcare deficit and spatial isolation most severe, and where will a new facility yield the maximum population coverage improvement?"*

```text
Healthcare Need (Population & Demographics across 898 Wards)
      ↓
Resource Gap (4-Factor Gap Score 0–100)
      ↓
Priority Wards & Healthcare Deserts (57.3% Desert Prevalence)
      ↓
Spatial Machine Learning (Leave-One-City-Out Cross-Validation)
      ↓
Candidate Site Generation (500m Spatial Grid in Deficit Voids)
      ↓
Candidate Ranking & Multi-Criteria Evaluation
      ↓
Decision Analytics (2SFCA, AHP Suitability, MCLP, AIPS Robustness)
      ↓
Independent RStudio Replication (r_project/ with 100% Numerical Parity)
      ↓
Interactive Multi-City Dashboard (Streamlit Pages 1–9)
```

---

## 2. Multi-City Geographic Coverage

CRADLE seamlessly manages coordinate reference systems (CRS) dynamically based on city longitude:

| Metropolitan City | State | Municipal Authority | Wards | Facilities | Population | Metric CRS | Central Meridian |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **Chennai** | Tamil Nadu | Greater Chennai Corporation (GCC) | 200 | 173 | 10.18 M | `EPSG:32644` (UTM 44N) | 81°E |
| **Coimbatore** | Tamil Nadu | Coimbatore City Municipal Corp (CCMC) | 100 | 89 | 2.66 M | `EPSG:32643` (UTM 43N) | 75°E |
| **Bengaluru** | Karnataka | Bruhat Bengaluru Mahanagara Palike (BBMP) | 198 | 171 | 13.73 M | `EPSG:32643` (UTM 43N) | 75°E |
| **Hyderabad** | Telangana | Greater Hyderabad Municipal Corp (GHMC) | 150 | 132 | 11.04 M | `EPSG:32644` (UTM 44N) | 81°E |
| **Delhi (NCT)** | Delhi | Municipal Corporation of Delhi (MCD) | 250 | 215 | 20.02 M | `EPSG:32643` (UTM 43N) | 75°E |
| **Total Corpus** | **4 States / UTs** | **5 Municipal Corporations** | **898** | **780** | **57.62 M** | **Multi-CRS** | - |

---

## 3. Core Methodological Contributions

### A. The 4-Indicator Healthcare Gap Score ($0 - 100$)
$$\text{Gap Score}_i = \left( 0.30 \cdot P_i + 0.30 \cdot C_i + 0.25 \cdot D_i + 0.15 \cdot S_i \right) \times 100$$
* **Population Pressure ($P_i$):** Density percentile ($70\%$) + vulnerable cohort ratio ($30\%$).
* **Capacity Deficit ($C_i$):** Bed shortage relative to WHO target ($3.0$ beds / 1,000 residents).
* **Distance Gap ($D_i$):** Travel distance to nearest primary clinic ($40\%$, target 2.5 km) and secondary hospital ($60\%$, target 5.0 km).
* **Facility Scarcity ($S_i$):** Primary clinics per 10,000 population.

### B. Spatial Machine Learning with Leave-One-City-Out (LOCO) CV
Random $k$-fold cross-validation causes spatial data leakage due to spatial autocorrelation between adjacent wards. CRADLE uses **Leave-One-City-Out (LOCO) Cross-Validation**, holding out an entire metropolitan city in each fold:
* **Spatial LOCO Classification Accuracy:** **85.08%** (Weighted F1: 0.8362)
* **Spatial LOCO Regressor RMSE:** **3.46** (Mean $R^2$: **0.929**)
* **Full Production Corpus Fit:** **99.69% accuracy**, $0.37$ RMSE ($R^2 = 0.999$)
* **Top Predictive Drivers:** `Beds_per_1000` (29.9%), `Nearest_Hospital_Distance` (16.6%), `Population_Density` (15.2%).

### C. Independent RStudio Replication Package (`r_project/`)
All formulas and spatial routines are replicated in native R (`sf`, `dplyr`, `readr`):
* **Gap Score Pearson Correlation:** $r = \mathbf{1.000000}$ ($\text{MAE} = 0.0000$)
* **Priority Classification Concordance:** $\mathbf{100.0\%}$
* **Healthcare Desert Concordance:** $\mathbf{100.0\%}$

### D. Operations Research & Robustness
* **Maximal Covering Location Problem (MCLP):** Integer program solved via `PuLP` branch-and-bound. Siting 5 facilities in Chennai covers **4.3M residents (42.3%)**.
* **Adaptive Infrastructure Planning Score (AIPS):** Evaluates candidate site robustness ($0 - 100$) across 4 competing planning regimes.

---

## 4. Directory Structure

```text
CRADLE/
├── app.py                      # Multi-city Streamlit dashboard portal
├── config.py                   # Multi-city registry, parameters, UTM CRSs
├── pytest.ini                 # Pytest runner configuration
├── requirements.txt            # Python dependencies
│
├── ARCHITECTURE.md             # Technical design & subsystem architecture
├── METHODOLOGY.md              # Mathematical formulations & Gap-First logic
├── DATA_DICTIONARY.md          # Complete schema specifications
├── DATA_SOURCES.md             # Provenance, municipal calibration & ingestion
├── TESTING_REPORT.md           # Test execution and verification results
├── PYTHON_R_VALIDATION.md      # Numerical parity report (Python vs R)
├── FINAL_REVIEW3_REPORT.md     # Final Review-3 report & defense talking points
│
├── data/
│   ├── raw/                    # Raw inputs (place official municipal files here)
│   ├── processed/              # Analysis-ready GeoJSONs (all cities & individual)
│   └── sample/                 # Calibrated multi-city datasets
│
├── models/                     # Trained ML model binaries (.joblib) & metadata
├── outputs/
│   ├── maps/                   # Generated maps
│   ├── reports/                # Markdown executive decision reports
│   ├── results/                # CSV rankings and MCLP selection tables
│   └── model_metrics/          # Confusion matrices, classification reports, LOCO JSON
│
├── pages/
│   ├── 1_Overview.py           # City demographics & Cross-City Benchmarking
│   ├── 2_Gap_Analyzer.py       # 4-factor gap choropleth & natural explainability
│   ├── 3_Healthcare_Deserts.py # Desert severity map & gravity facility strain
│   ├── 4_Candidate_Finder.py   # 500m candidate grid & multi-criteria ranking
│   ├── 5_Scenario_Simulator.py # Interactive Before vs After investment simulation
│   ├── 6_Accessibility.py      # 2SFCA accessibility & road travel isochrones
│   ├── 7_Optimization.py       # MCLP integer optimizer, budget scenarios & AIPS
│   ├── 8_Machine_Learning.py   # Spatial LOCO CV metrics & interactive predictor
│   └── 9_Data_Quality.py       # Provenance audit, null checks & Python-vs-R parity
│
├── r_project/                  # Standalone RStudio replication environment
│   ├── CRADLE_R.Rproj          # RStudio Project File
│   ├── README.md               # RStudio instructions & package setup
│   ├── data/                   # Synchronized multi-city GeoJSON and CSV data
│   ├── scripts/                # 01_load_data.R through 06_validate_against_python.R
│   └── outputs/                # R validation tables
│
├── scripts/
│   ├── generate_sample_data.py # Synthesizes 648 wards across 4 cities
│   ├── preprocess_data.py      # Multi-city preprocessing & spatial joins
│   ├── export_to_r_project.py  # Copies datasets to r_project/data/
│   ├── validate_r_output.py    # Cross-platform numerical verification
│   └── run_pipeline.py         # Headless end-to-end execution runner
│
├── src/                        # 14 modular analytical engines
│   ├── data_loader.py          # Schema validation & multi-city loading
│   ├── preprocessing.py        # Spatial joins & metric projection
│   ├── gap_analyzer.py         # 4-factor gap score & explainability
│   ├── healthcare_desert.py    # Multi-criteria desert detector
│   ├── facility_pressure.py    # Gravity load allocation
│   ├── candidate_generator.py  # 500m candidate grid in deficit voids
│   ├── candidate_ranking.py    # Multi-criteria candidate scoring
│   ├── coverage.py             # Concentric buffer population catchment
│   ├── scenario.py             # Before vs After simulation engine
│   ├── accessibility.py        # Road routing & isochrones
│   ├── two_sfca.py             # Two-Step Floating Catchment Area model
│   ├── ahp.py                  # AHP & Fuzzy AHP physical suitability
│   ├── mclp.py                 # Maximal Covering Location Problem optimizer
│   ├── sensitivity.py          # Weight profile sensitivity analysis
│   ├── aips.py                 # AIPS robustness index
│   ├── intervention.py         # Policy intervention recommender
│   ├── model_training.py       # Leave-One-City-Out Spatial CV training
│   ├── model_evaluation.py     # Metrics, confusion matrix, feature importance
│   └── model_inference.py      # Production predictor API
│
└── tests/                      # Automated test suite (17 passed)
    ├── test_gap.py             # Gap score, desert detection, explainability
    ├── test_candidate.py       # Candidate generation, ranking, fallbacks
    ├── test_coverage.py        # Catchment coverage & scenario simulation
    ├── test_ml.py              # ML inference, batch prediction, metadata
    └── test_multi_city.py      # Multi-city CRS, isolation & composite IDs
```

---

## 5. Installation & Quick Start

### Step 1: Clone & Navigate
```powershell
cd C:\Users\Asus\.gemini\antigravity\scratch\CRADLE
```

### Step 2: Activate Environment & Install Dependencies
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3: Run Full Automated Test Suite (17 Tests)
```powershell
pytest tests/ -v
```

### Step 4: Run End-to-End Pipeline
```powershell
python scripts/run_pipeline.py --city chennai
```
This executes multi-city data preprocessing, LOCO machine learning training and evaluation, RStudio synchronization, Python-vs-R numerical validation, MCLP optimization, and exports reports.

### Step 5: Launch Interactive Web Dashboard
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 6. Academic Reference & Citation

* **Deepthika C., Aruna S.** (2026), *"CRADLE: Critical Resource Allocation, Distribution & Location Engine"*, Department of Software Engineering, School of Information Technology and Engineering, Vellore Institute of Technology (VIT), Chennai.
