# CRADLE: Critical Resource Allocation, Distribution & Location Engine
## Executive Decision-Support & Healthcare Siting Report
**Location:** Greater Chennai Corporation (GCC), Tamil Nadu, India  
**Planning Methodology:** Gap-First Spatial Allocation Framework  

---

## 1. Executive Summary & Baseline Diagnosis
- **Total Population:** 9,514,495 residents across 200 wards in 15 zones.
- **Existing Healthcare Infrastructure:** 184 total facilities, 12,383 inpatient beds.
- **Current Capacity Ratio:** **1.3 beds per 1,000 population** (Standard WHO Target: 3.0 beds per 1,000).
- **Critical Priority Wards:** **15 wards** experiencing acute capacity, distance, and density strain.
- **Identified Healthcare Deserts:** **76 wards** (38.0% of city) housing **3,878,159 citizens**.

---

## 2. Top Priority Underserved Wards (Resource Gap Ranking)
| Rank | Ward ID | Ward Name | Zone | Population | Beds/1000 | Hospital Dist (km) | Gap Score | Priority | Primary Diagnostic |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 67 | Ward 067 | Thiru-Vi-Ka Nagar | 56,856 | 0.0 | 0.96 | **74.2** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 1 | 123 | Ward 123 | Teynampet | 75,000 | 0.0 | 1.61 | **74.2** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 3 | 38 | Ward 038 | Tondiarpet | 74,902 | 0.0 | 0.82 | **74.1** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 4 | 45 | Ward 045 | Tondiarpet | 61,163 | 0.0 | 1.24 | **73.2** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 4 | 46 | Ward 046 | Tondiarpet | 64,336 | 0.0 | 1.11 | **73.2** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 6 | 17 | Ward 017 | Manali | 21,210 | 0.0 | 5.8 | **72.8** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 7 | 64 | Ward 064 | Thiru-Vi-Ka Nagar | 67,183 | 0.0 | 0.79 | **72.7** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |
| 8 | 91 | Ward 091 | Ambattur | 44,970 | 0.0 | 7.98 | **72.6** | Critical | Severe shortage of hospital beds and secondary clinical capacity relative to population. |

---

## 3. Recommended Primary Site: Candidate C748
- **Candidate Location:** Lat 13.13619, Lon 80.29375 (Ward 038, Tondiarpet)
- **Composite Candidate Score:** **73.4/100** (Recommended)
- **Ward Gap Severity:** 74.1/100
- **Catchment Population (3km Radius):** **1,214,197 residents** across 30 wards.
- **Distance to Nearest Existing Facility:** 0.95 km (mitigates spatial vacuum).
- **AHP Physical Site Suitability:** 68.6/100 (Suitable)
- **Recommended Intervention:** **Tier 2 Priority - Community Health Centre**
  - Facility Type: `CHC`
  - Target Capacity: `40 Beds`
  - Estimated Capital Expenditure: `₹8.0 Crores`

---

## 4. Multi-Facility Optimal Network Solution (MCLP Optimization)
Under a portfolio allocation of **5 facilities** within a 3.0 km service radius:
- **Selected Candidate Sites:** `C814, C1524, C1340, C942, C1886`
- **System Population Coverage:** **5,404,409 citizens** (**56.8%** coverage)
- **Critical & High Gap Wards Remediated:** 67 wards
- **Total Capital Allocation:** ₹40.0 Crores

---

## 5. Decision Robustness & AIPS Verification
Top robust candidate locations verified across 4 sensitivity scenarios (Population-focused, Capacity-focused, Accessibility-focused, Balanced):

| Candidate ID | Ward Name | Zone | Baseline Rank | AIPS Score | Robustness Category | Cross-Scenario StdDev |
|---|---|---|---|---|---|---|
| C155 | Ward 006 | Thiruvottiyur | #138 | **62.7** | **Moderately Robust** | ±7.0 |
| C1367 | Ward 106 | Anna Nagar | #64 | **61.9** | **Moderately Robust** | ±7.7 |
| C156 | Ward 006 | Thiruvottiyur | #153 | **60.7** | **Moderately Robust** | ±11.7 |
| C1785 | Ward 168 | Adyar | #132 | **60.6** | **Moderately Robust** | ±13.1 |
| C940 | Ward 072 | Thiru-Vi-Ka Nagar | #123 | **60.4** | **Moderately Robust** | ±13.9 |
| C1788 | Ward 168 | Adyar | #64 | **60.3** | **Moderately Robust** | ±9.6 |

---
*Report generated automatically by CRADLE Spatial Decision-Support Engine.*