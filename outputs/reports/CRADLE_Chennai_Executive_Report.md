# CRADLE: Critical Resource Allocation, Distribution & Location Engine
## Executive Decision-Support & Healthcare Siting Report: Chennai
**Jurisdiction:** Greater Chennai Corporation (GCC), Tamil Nadu, India  
**Planning Methodology:** Gap-First Spatial Allocation & Multi-Criteria Integer Optimization  
**Spatial Reference:** WGS84 Geographic / UTM Metric (EPSG:32644)  

---

## 1. Executive Summary & Baseline Diagnosis
- **Total Population:** 10,178,719 residents across 200 wards (15 administrative zones).
- **Existing Healthcare Infrastructure:** 173 clinical facilities, 8,804 inpatient beds.
- **Current Capacity Ratio:** **0.86 beds per 1,000 population** (Standard WHO Target: 3.0 beds per 1,000).
- **Critical Priority Wards:** **26 wards** experiencing acute capacity, distance, and density strain.
- **Identified Healthcare Deserts:** **96 wards** housing **5,025,888 underserved residents**.
- **Spatial Machine Learning Performance:** **85.1% LOCO Accuracy**, Regressor RMSE **3.55**.

---

## 2. Top Priority Underserved Wards (Resource Gap Ranking)
| Rank | Ward ID | Ward Name | Zone | Population | Beds/1000 | Hospital Dist (km) | Gap Score | Priority | Primary Diagnostic |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 67 | Periamet (Ward 067) | Royapuram | 47,436 | 0.00 | 5.55 | **86.4** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 2 | 69 | Ripon Building Area (Ward 069) | Royapuram | 49,171 | 0.00 | 5.83 | **83.9** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 3 | 43 | Kodungaiyur East (Ward 043) | Tondiarpet | 52,469 | 0.00 | 5.03 | **77.4** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 4 | 27 | Manali Sector 13 (Ward 027) | Manali | 74,727 | 0.00 | 1.07 | **75.1** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 5 | 14 | Tiruvottiyur Market (Ward 014) | Thiruvottiyur | 69,979 | 0.00 | 1.25 | **74.9** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 6 | 197 | Sholinganallur Sector 10 (Ward 197) | Sholinganallur | 49,173 | 0.00 | 1.36 | **74.8** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 7 | 95 | Venkatapuram (Ward 095) | Ambattur | 54,181 | 0.00 | 1.18 | **74.2** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 8 | 182 | Puzhuthivakkam (Ward 182) | Perungudi | 51,078 | 0.00 | 1.23 | **73.9** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |

---

## 3. Recommended Primary Site: Candidate C378
- **Candidate Location:** Lat 13.23124, Lon 80.26819 (Kondithope (Ward 061), Royapuram)
- **Composite Candidate Score:** **75.2/100** (Highly Recommended)
- **Ward Gap Severity:** 72.8/100
- **Catchment Population (3km Radius):** **702,870 residents** across 21 wards.
- **Distance to Nearest Existing Facility:** 1.52 km (mitigates spatial vacuum).
- **AHP Physical Site Suitability:** 74.1/100 (Suitable)
- **Recommended Intervention:** **Tier 1 Priority - Major Facility Construction**
  - Facility Type: `Government Hospital`
  - Target Capacity: `150 Beds`
  - Estimated Capital Expenditure: `₹25.0 Crores`

---

## 4. Multi-Facility Optimal Network Solution (MCLP Optimization)
Under a portfolio allocation of **5 facilities** within a 3.0 km service radius:
- **Selected Candidate Sites:** `C104, C472, C2338, C2618, C172`
- **System Population Coverage:** **4,305,132 citizens** (**42.3%** coverage)
- **Critical & High Gap Wards Remediated:** 68 wards
- **Total Capital Allocation:** ₹40.0 Crores

---

## 5. Decision Robustness & AIPS Verification
Top robust candidate locations verified across 4 sensitivity regimes:

| Candidate ID | Ward Name | Zone | Baseline Rank | AIPS Score | Robustness Category | Cross-Scenario StdDev |
|---|---|---|---|---|---|---|
| C075 | Chinna Sekkadu (Ward 021) | Manali | #49 | **65.8** | **Robust** | ±4.8 |
| C072 | Chinna Sekkadu (Ward 021) | Manali | #43 | **65.3** | **Robust** | ±5.0 |
| C111 | Manali Sector 14 (Ward 028) | Manali | #73 | **64.9** | **Robust** | ±6.4 |
| C062 | Manali New Town (Ward 018) | Manali | #77 | **63.5** | **Moderately Robust** | ±8.8 |
| C064 | Manali New Town (Ward 018) | Manali | #75 | **63.5** | **Moderately Robust** | ±8.3 |
| C108 | Manali Sector 12 (Ward 026) | Manali | #82 | **62.9** | **Moderately Robust** | ±9.7 |

---
*Report generated automatically by CRADLE Review-3 Multi-City Engine for Chennai.*