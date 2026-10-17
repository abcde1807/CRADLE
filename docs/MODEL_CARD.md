# CRADLE Model Card: Healthcare Gap & Priority Classification

## 1. Model Details

- **Model Name:** CRADLE Spatial Healthcare Gap & Priority Estimator
- **Model Version:** 1.0.0
- **Model Date:** October 2026 (CRADLE Review-3)
- **Model Architecture:**
  - **Classification Model:** Random Forest Classifier (150 estimators, max depth 12, min samples split 4, balanced weights).
  - **Regression Model:** Gradient Boosting Regressor (120 estimators, max depth 5, learning rate 0.08).
  - **Feature Scaling:** `StandardScaler` preprocessing pipeline fit on tabular demographic and spatial features.
- **Repository / Workspace:** `CRADLE/models/`
- **Model Artifacts:**
  - `cradle_priority_classifier.joblib`
  - `cradle_gap_regressor.joblib`
  - `cradle_ml_preprocessor.joblib`
  - `cradle_feature_names.json`
  - `outputs/model_metrics/spatial_loco_evaluation.json`

---

## 2. Intended Use & Application Scope

- **Primary Objective:** Predict ward-level Healthcare Priority Category (`Low`, `Moderate`, `High`, `Critical`) and continuous Healthcare Gap Score (0–100) based on municipal demographics and spatial facility access indicators.
- **Intended Users:** Urban healthcare planners, public health administrators, municipal corporation health officers, and GIS analysts.
- **Out-of-Scope Use:** The model is a **decision-support tool** and must not be used as an autonomous resource allocator without human epidemiological oversight. It is not designed for individual patient triage or clinical diagnostic workflows.

---

## 3. Training & Evaluation Data

- **Geographic Scope:** 5 Metropolitan Cities across India:
  1. **Chennai, Tamil Nadu** (200 wards, ~10.2M population, UTM 44N - EPSG:32644)
  2. **Coimbatore, Tamil Nadu** (100 wards, ~2.7M population, UTM 43N - EPSG:32643)
  3. **Bengaluru, Karnataka** (198 wards, ~13.7M population, UTM 43N - EPSG:32643)
  4. **Hyderabad, Telangana** (150 wards, ~11.0M population, UTM 44N - EPSG:32644)
  5. **Delhi (NCT), Delhi** (250 wards, ~20.0M population, UTM 43N - EPSG:32643)
- **Total Training Samples:** 898 administrative wards.
- **Data Provenance:** Synthetic development datasets rigorously calibrated to official 2024 municipal corporation statistical abstracts (GCC, CCMC, BBMP, GHMC, MCD) and Census of India demographic distributions. Every ward is identified by an authentic neighborhood/locality name.
- **Features Used (10 features):**
  1. `Population`: Total resident ward population
  2. `Population_Density`: Population per square kilometer
  3. `Elderly`: Population aged 60+
  4. `Children`: Population aged 0–6
  5. `Households`: Estimated household count
  6. `Vuln_Ratio`: Vulnerable population dependency ratio `(Elderly + Children) / Population`
  7. `Nearest_Facility_Distance`: Euclidean distance to nearest healthcare center (km)
  8. `Nearest_Hospital_Distance`: Euclidean distance to nearest secondary/tertiary hospital (km)
  9. `Healthcare_Facilities`: Facility count within administrative ward boundary
  10. `Beds_per_1000`: Ratio of hospital beds per 1,000 residents

---

## 4. Evaluation Strategy: Leave-One-City-Out Spatial Cross-Validation

Standard random k-fold cross-validation is **invalid for spatial systems** because spatial autocorrelation (Tobler's First Law of Geography) leaks information between adjacent training and test wards, yielding artificially inflated accuracy.

To prove genuine spatial generalizability across Indian metropolitan regions, CRADLE utilizes **Leave-One-City-Out (LOCO) Spatial Cross-Validation** (5 folds, where an entire metropolitan city is held out as the test set):

| Fold | Holdout Test City | State | Wards | Classification Accuracy | Weighted F1 | Regression RMSE | Regression $R^2$ |
|:----:|:-----------------:|:-----:|:-----:|:-----------------------:|:-----------:|:---------------:|:----------------:|
| 1 | **Bengaluru** | Karnataka | 198 | 82.8% | 0.801 | 3.49 | 0.906 |
| 2 | **Chennai** | Tamil Nadu | 200 | 85.0% | 0.854 | 3.13 | 0.938 |
| 3 | **Coimbatore** | Tamil Nadu | 100 | 81.0% | 0.768 | 5.16 | 0.908 |
| 4 | **Delhi (NCT)** | Delhi | 250 | 87.2% | 0.874 | 3.86 | 0.849 |
| 5 | **Hyderabad** | Telangana | 150 | 89.3% | 0.885 | 2.13 | 0.960 |
| **Mean** | **Multi-City LOCO** | - | **898** | **85.07%** | **0.8366** | **3.55** | **0.912** |

### Full Corpus Performance (Fitted Production Model)

- **Overall Classification Accuracy:** 99.67%
- **Weighted F1-Score:** 0.9966
- **Regression RMSE:** 0.69 (Continuous 0–100 scale)
- **Regression $R^2$ Score:** 0.997

---

## 5. Feature Importances (Top Predictive Drivers)

The Random Forest feature importance analysis reveals the governing drivers of healthcare gap vulnerability:

1. **`Beds_per_1000` (30.1%):** Bed capacity deficit relative to the WHO 3.0 benchmark is the dominant predictor of ward-level strain.
2. **`Nearest_Hospital_Distance` (16.7%):** Spatial distance to secondary/emergency care strongly dictates whether a ward is classified as High/Critical.
3. **`Population_Density` (15.8%):** Dense informal settlements experience severe facility congestion.
4. **`Nearest_Facility_Distance` (11.2%):** Proximity to primary health posts.
5. **`Vuln_Ratio` (8.5%):** Proportions of geriatric and pediatric residents increase localized demand.

---

## 6. Confusion Matrix (Production Fit)

```text
Actual \ Pred      Low    Moderate    High    Critical
Low                 20           0       0           0
Moderate             0         132       0           0
High                 0           0     601           0
Critical             0           0       3         142
```

- Precision on `Critical` Priority: **100.0%**
- Recall on `Critical` Priority: **97.9%**
- F1-Score on `Critical` Priority: **0.989**

---

## 7. Limitations & Caveats

1. **Synthetic Data Calibration:** Current weights and models are calibrated against realistic synthetic distributions mirroring 2024 municipal statistics. Deployment in real municipal workflows should incorporate live HMIS (Health Management Information System) and OpenStreetMap road vectors.
2. **Euclidean vs Road Network Distances:** While the core ML features currently utilize Euclidean spatial metrics for cross-city speed, actual travel times in dense Indian corridors may be influenced by peak traffic congestion and public transit connectivity.
3. **Boundary Effects:** Wards adjacent to municipal corporation boundaries may access hospitals in contiguous peri-urban or panchayat jurisdictions not captured in the municipal ward polygon.
