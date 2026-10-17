# CRADLE Changelog

All notable changes to the CRADLE project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.1.0] - 2026-10-17 (5-City Metropolitan Expansion & Authentic Locality Upgrade)

### Added
- **5th Metropolitan City Added - Delhi (National Capital Territory)**:
  - 250 administrative wards across 12 zones administered by Municipal Corporation of Delhi (MCD).
  - UTM Zone 43N metric projection (`EPSG:32643`), bounding box, and 2024 MCD statistical calibration.
  - 12 real landmark hospitals (AIIMS, Safdarjung, RML, LNJP, GTB, Sir Ganga Ram, Max Saket, Apollo Sarita Vihar, Fortis Escorts, Rajiv Gandhi, DDU, BLK-Max).
- **Authentic Locality & Neighborhood Naming Across All 5 Cities**:
  - Replaced generic "Ward 001" labels with authentic, recognized locality names across all 898 wards:
    - **Bengaluru (BBMP - 198 Wards)**: Koramangala, Indiranagar, Malleshwaram, HSR Layout, BTM Layout, Whitefield, Marathahalli, Jayanagar, Basavanagudi, etc.
    - **Coimbatore (CCMC - 100 Wards)**: RS Puram, Gandhipuram, Peelamedu, Singanallur, Saibaba Colony, Ramanathapuram, Ukkadam, Saravanampatti, etc.
    - **Hyderabad (GHMC - 150 Wards)**: Banjara Hills, Jubilee Hills, Madhapur, Gachibowli, Hitec City, Begumpet, Charminar, Secunderabad, Kukatpally, etc.
    - **Delhi (MCD - 250 Wards)**: Connaught Place, Chanakyapuri, Defence Colony, Lajpat Nagar, Greater Kailash, Hauz Khas, Saket, Dwarka, Rohini, Karol Bagh, etc.
    - **Chennai (GCC - 200 Wards)**: George Town, Royapuram, Tondiarpet, Kilpauk, Anna Nagar, T. Nagar, Mylapore, Adyar, Velachery, Sholinganallur, etc.
- **5-Fold Leave-One-City-Out Spatial Cross Validation**:
  - Evaluated on 898 total wards across 5 holdout cities: 85.07% classification accuracy, 0.8366 weighted F1, 3.55 RMSE, 0.912 $R^2$.
- **Synchronized RStudio Replication Package**:
  - Re-exported all 5 cities to `r_project/data/` with 100% numerical parity ($r = 1.000000$, MAE = 0.0000).

## [3.0.0] - 2026-10-17 (Review-3 Final Delivery)

### Added
- **Multi-City Configuration Registry (`config.py`)**:
  - Full operational support for **Chennai (TN)**, **Coimbatore (TN)**, **Bengaluru (KA)**, and **Hyderabad (TS)**.
  - Distinct coordinate reference systems: UTM Zone 44N (`EPSG:32644`) for Eastern/Central cities; UTM Zone 43N (`EPSG:32643`) for Western/Southern cities.
  - Multi-city bounding boxes, zone anchors, and demographic baselines.
- **Multi-City Data Generator (`scripts/generate_sample_data.py`)**:
  - Synthesizes 648 total wards across 4 cities (Chennai: 200, Coimbatore: 100, Bengaluru: 198, Hyderabad: 150).
  - Synthesizes 565 healthcare facilities across all tiers (General, District, CHC, UPHC, PHC, Private).
  - Uniform composite administrative keys (`Country`, `State`, `City`, `Administrative_Area_ID`, `Administrative_Area_Name`, `Zone`).
- **Machine Learning Pipeline (`src/model_training.py`, `src/model_evaluation.py`, `src/model_inference.py`)**:
  - Random Forest and Gradient Boosting models for priority classification and gap severity regression.
  - **Leave-One-City-Out Spatial Cross-Validation** to eliminate spatial leakage.
  - Saved model binaries in `models/` and evaluation metrics in `outputs/model_metrics/`.
  - Comprehensive model documentation in `docs/MODEL_CARD.md`.
- **RStudio Replication Framework (`r_project/`)**:
  - Complete R project `CRADLE_R.Rproj`.
  - Independent R scripts using `sf`, `dplyr`, `tidyr`, `readr`, `ggplot2`.
  - Shared data exports in `r_project/data/`.
  - Python-to-R validation report (`PYTHON_R_VALIDATION.md`).
- **Dashboard Enhancements**:
  - Global City and State selector across all pages.
  - Cross-City Comparison and Benchmarking view in Page 1 (`1_Overview.py`).
  - New Page 8: Machine Learning Insights & Demographic Predictor (`8_Machine_Learning.py`).
  - New Page 9: Data Provenance, Quality & Validation (`9_Data_Quality.py`).
- **Comprehensive Academic Documentation**:
  - `PROJECT_AUDIT.md`, `IMPLEMENTATION_STATUS.md`, `ARCHITECTURE.md`, `METHODOLOGY.md`, `DATA_DICTIONARY.md`, `DATA_SOURCES.md`, `TESTING_REPORT.md`, `PYTHON_R_VALIDATION.md`, `FINAL_REVIEW3_REPORT.md`.

### Changed
- Parameterized `DataLoader`, `PreprocessingPipeline`, and spatial analytics modules with `city_key`.
- Updated tile providers to `OpenStreetMap` for reliable, API-key-free map rendering.

---

## [2.0.0] - 2026-09-18 (Phase 2 & Phase 3 Advanced Analytics)

### Added
- NetworkX road network topological routing and 5/10/15-minute driving isochrones.
- Two-Step Floating Catchment Area (2SFCA) spatial accessibility model.
- Analytic Hierarchy Process (AHP) and Fuzzy AHP physical site suitability overlay.
- Maximal Covering Location Problem (MCLP) binary integer linear programming optimizer using PuLP.
- Budget allocation scenarios (₹15 Cr, ₹35 Cr, ₹80 Cr).
- Sensitivity analysis across 4 planning regimes and Adaptive Infrastructure Planning Score (AIPS) robustness engine.

---

## [1.0.0] - 2026-09-14 (Phase 1 Baseline Implementation)

### Added
- Initial single-city Chennai 4-factor Healthcare Gap Score ($0–100$).
- Healthcare Desert Detection and Huff Gravity Facility Pressure module.
- 500m candidate location generator with 600m exclusion buffers.
- Concentric buffer coverage analysis (2 km, 3 km, 5 km).
- Before vs. After scenario simulator with $\Delta\text{Gap}$ calculations.
- Multi-page Streamlit interactive dashboard (`app.py`, pages 1 to 7).
- 10 automated unit test cases with PyTest.
