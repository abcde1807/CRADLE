# CRADLE: Critical Resource Allocation, Distribution & Location Engine
## Executive Decision-Support & Healthcare Siting Report: Delhi (NCT)
**Jurisdiction:** Municipal Corporation of Delhi (MCD), Delhi, India  
**Planning Methodology:** Gap-First Spatial Allocation & Multi-Criteria Integer Optimization  
**Spatial Reference:** WGS84 Geographic / UTM Metric (EPSG:32643)  

---

## 1. Executive Summary & Baseline Diagnosis
- **Total Population:** 20,023,500 residents across 250 wards (12 administrative zones).
- **Existing Healthcare Infrastructure:** 215 clinical facilities, 17,104 inpatient beds.
- **Current Capacity Ratio:** **0.85 beds per 1,000 population** (Standard WHO Target: 3.0 beds per 1,000).
- **Critical Priority Wards:** **33 wards** experiencing acute capacity, distance, and density strain.
- **Identified Healthcare Deserts:** **148 wards** housing **11,966,931 underserved residents**.
- **Spatial Machine Learning Performance:** **85.1% LOCO Accuracy**, Regressor RMSE **3.55**.

---

## 2. Top Priority Underserved Wards (Resource Gap Ranking)
| Rank | Ward ID | Ward Name | Zone | Population | Beds/1000 | Hospital Dist (km) | Gap Score | Priority | Primary Diagnostic |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 241 | Laxmi Nagar Metro (Ward 241) | Shahdara South | 92,193 | 0.00 | 3.76 | **82.1** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 2 | 28 | Hauz Khas Village (Ward 028) | South Zone | 95,000 | 0.00 | 2.47 | **77.9** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 3 | 17 | Andrews Ganj (Ward 017) | Central Zone | 95,000 | 0.08 | 2.72 | **76.3** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 4 | 174 | Rampura (Ward 174) | Keshav Puram | 79,495 | 0.00 | 4.88 | **74.4** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 4 | 189 | Kanhaiya Nagar (Ward 189) | Keshav Puram | 95,000 | 0.00 | 4.66 | **74.4** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 6 | 1 | Connaught Place (Ward 001) | Central Zone | 95,000 | 0.00 | 3.48 | **74.3** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 7 | 14 | South Extension Part 2 (Ward 014) | Central Zone | 95,000 | 0.00 | 2.13 | **74.0** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 8 | 238 | Preet Vihar Main (Ward 238) | Shahdara South | 95,000 | 0.34 | 3.30 | **73.9** | Critical | Acute lack of primary and urban community healthcare centres. |

---

## 3. Recommended Primary Site: Candidate C120
- **Candidate Location:** Lat 28.61752, Lon 77.30720 (Kotla Mubarakpur (Ward 015), Central Zone)
- **Composite Candidate Score:** **81.8/100** (Highly Recommended)
- **Ward Gap Severity:** 69.7/100
- **Catchment Population (3km Radius):** **575,457 residents** across 13 wards.
- **Distance to Nearest Existing Facility:** 3.70 km (mitigates spatial vacuum).
- **AHP Physical Site Suitability:** 87.7/100 (Highly Suitable)
- **Recommended Intervention:** **Tier 1 Priority - Major Facility Construction**
  - Facility Type: `Government Hospital`
  - Target Capacity: `150 Beds`
  - Estimated Capital Expenditure: `₹25.0 Crores`

---

## 4. Multi-Facility Optimal Network Solution (MCLP Optimization)
Under a portfolio allocation of **5 facilities** within a 3.0 km service radius:
- **Selected Candidate Sites:** `C889, C8596, C100, C475, C8641`
- **System Population Coverage:** **5,366,527 citizens** (**26.8%** coverage)
- **Critical & High Gap Wards Remediated:** 57 wards
- **Total Capital Allocation:** ₹40.0 Crores

---

## 5. Decision Robustness & AIPS Verification
Top robust candidate locations verified across 4 sensitivity regimes:

| Candidate ID | Ward Name | Zone | Baseline Rank | AIPS Score | Robustness Category | Cross-Scenario StdDev |
|---|---|---|---|---|---|---|
| C8588 | Vivek Vihar Phase 2 (Ward 234) | Shahdara South | #152 | **64.8** | **Sensitive** | ±15.8 |
| C8237 | Seelampur Metro (Ward 211) | Shahdara North | #181 | **64.7** | **Sensitive** | ±17.1 |
| C879 | Vikas Puri Block F (Ward 053) | West Zone | #81 | **64.5** | **Moderately Robust** | ±11.7 |
| C8233 | Seelampur Metro (Ward 211) | Shahdara North | #162 | **63.9** | **Sensitive** | ±19.0 |
| C884 | Vikas Puri Block F (Ward 053) | West Zone | #100 | **63.8** | **Sensitive** | ±15.3 |
| C8607 | Anand Vihar ISBT (Ward 236) | Shahdara South | #45 | **63.8** | **Moderately Robust** | ±9.8 |

---
*Report generated automatically by CRADLE Review-3 Multi-City Engine for Delhi (NCT).*