# CRADLE Data Dictionary & Schema Specification

## 1. Ward Layer Schema (`processed_{city}_wards.geojson` & `all_cities_wards.geojson`)

| Field Name | Data Type | Units / Range | Description | Example Value |
|---|---|---|---|---|
| `Composite_ID` | String | Format: `IND_{State}_{City}_{ID}` | Unique pan-Indian primary key | `IND_TN_CHN_001` |
| `Ward_ID` | Integer | City-specific integer | Municipal administrative ward identifier | `1` |
| `Ward_Name` | String | Text | Official municipal ward name | `Kathivakkam` |
| `Zone` | String | Text | Municipal administrative zone name | `Thiruvottiyur` |
| `City` | String | Text | Metropolitan city name | `Chennai` |
| `City_Key` | String | Lowercase key | Normalized system city slug | `chennai` |
| `State` | String | Text | Indian State | `Tamil Nadu` |
| `State_Code` | String | 2-Letter ISO | Indian State postal code | `TN` |
| `Country` | String | Text | Sovereign nation | `India` |
| `Population` | Integer | Persons | Total resident population | `54,320` |
| `Area_km2` | Float | $\text{km}^2$ | Geographic area of the ward | `3.45` |
| `Population_Density`| Float | $\text{persons}/\text{km}^2$ | Population per square kilometer | `15,744.9` |
| `Elderly` | Integer | Persons | Residents aged 60 and older | `5,432` |
| `Children` | Integer | Persons | Residents aged 0 to 6 years | `8,148` |
| `Households` | Integer | Count | Estimated household count | `13,580` |
| `Healthcare_Facilities`| Integer | Count | Clinical facilities within ward boundary | `2` |
| `Hospital_Beds` | Integer | Inpatient beds | Total registered beds in ward | `45` |
| `Beds_per_1000` | Float | Beds / 1,000 pop | Inpatient bed capacity ratio | `0.83` |
| `Nearest_Facility_Distance` | Float | Kilometers (km) | Geodesic distance to nearest primary clinic | `1.42` |
| `Nearest_Hospital_Distance` | Float | Kilometers (km) | Geodesic distance to nearest secondary/tertiary hospital | `4.85` |
| `Pop_Pressure_Norm`| Float | $0.0 - 100.0$ | Normalized demographic demand pressure | `68.5` |
| `Capacity_Deficit_Norm` | Float | $0.0 - 100.0$ | Normalized bed deficit relative to WHO 3.0 | `72.3` |
| `Distance_Gap_Norm` | Float | $0.0 - 100.0$ | Normalized spatial distance impedance | `58.2` |
| `Facility_Scarcity_Norm` | Float | $0.0 - 100.0$ | Normalized clinic deficit per 10k pop | `63.1` |
| `Gap_Score` | Float | $0.0 - 100.0$ | Composite 4-factor Healthcare Gap Score | `67.5` |
| `Priority_Category` | Categorical | `Low`, `Moderate`, `High`, `Critical` | Municipal resource allocation priority tier | `High` |
| `Primary_Issue` | String | Text | Dominant contributing factor to gap score | `Capacity Deficit` |
| `Explainability_Text`| String | Text | Natural-language policy diagnostic summary | *"Ward has severe capacity deficit..."* |
| `Healthcare_Desert` | Boolean | `True` / `False` | Multi-criteria healthcare desert flag | `True` |
| `Healthcare_Desert_Severity` | Float | $0.0 - 100.0$ | Severity index for identified deserts | `64.2` |
| `Desert_Affected_Population` | Integer | Persons | Population residing in desert wards | `54,320` |
| `Two_SFCA_Score` | Float | Ratio | Raw 2SFCA accessibility score | `0.0018` |
| `Two_SFCA_Norm` | Float | $0.0 - 100.0$ | Normalized 2SFCA spatial accessibility index | `38.4` |
| `Accessibility_Tier`| Categorical | 5 Tiers | 2SFCA classification | `Low Access` |
| `geometry` | Geometry | Polygon / MultiPolygon | Ward administrative boundary coordinates | `POLYGON ((...))` |

---

## 2. Healthcare Facility Schema (`processed_{city}_facilities.geojson`)

| Field Name | Data Type | Description | Allowed Values / Range | Example |
|---|---|---|---|---|
| `Facility_ID` | String | Unique facility identifier | `FAC_001` - `FAC_999` | `FAC_042` |
| `Facility_Name` | String | Official clinic/hospital name | Text | `Apollo Specialty Clinic` |
| `Facility_Type` | Categorical | Healthcare service tier | `PHC`, `UPHC`, `CHC`, `Government Hospital`, `General Hospital`, `Multi-Speciality Hospital`, `Private Clinic` | `UPHC` |
| `Ownership` | Categorical | Administrative governance | `Public`, `Private` | `Public` |
| `Level` | Integer | Clinical care hierarchy | `1` (Primary) to `4` (Tertiary) | `1` |
| `Beds` | Integer | Inpatient bed capacity | $0$ to $1,500$ beds | `12` |
| `Doctors` | Integer | On-duty medical officer count | $1$ to $150$ doctors | `3` |
| `Latitude` | Float | WGS84 Geographic Latitude | Decimal degrees | `13.0827` |
| `Longitude` | Float | WGS84 Geographic Longitude | Decimal degrees | `80.2707` |
| `Estimated_Pop_Served` | Integer | Allocated gravity catchment demand | Estimated persons | `42,180` |
| `Pressure_Ratio` | Float | Allocated demand / rated capacity | Ratio ($0.0 - 15.0+$) | `3.42` |
| `Pressure_Category` | Categorical | Operating strain classification | `Low`, `Moderate`, `High`, `Critical` | `High` |
| `geometry` | Geometry | Geographic Point | `POINT (Lon Lat)` | `POINT (80.27 13.08)` |

---

## 3. Candidate Facility Site Schema (`candidate_rankings.csv`)

| Field Name | Data Type | Range | Description |
|---|---|---|---|
| `Candidate_ID` | String | `C001` - `C999` | Candidate location identifier |
| `Ward_ID` | Integer | City-specific | Host municipal ward ID |
| `Ward_Name` | String | Text | Host municipal ward name |
| `Zone` | String | Text | Host administrative zone |
| `City_Key` | String | Text | Target metropolitan city |
| `Latitude` | Float | Decimal degrees | Proposed site latitude |
| `Longitude` | Float | Decimal degrees | Proposed site longitude |
| `Gap_Score` | Float | $0.0 - 100.0$ | Healthcare gap score of host ward |
| `Facility_Distance_km` | Float | Kilometers | Distance to nearest existing clinic |
| `Population_Covered` | Integer | Persons | Estimated residents within 3km catchment |
| `Wards_Reached` | Integer | Count | Count of distinct wards intersected |
| `Candidate_Score` | Float | $0.0 - 100.0$ | Multi-criteria priority siting score |
| `Rank` | Integer | $1, 2, 3, \dots$ | Systemwide ranking based on score |
| `Recommendation` | Categorical | Tiers | `Highly Recommended`, `Recommended`, `Marginal` |
| `AHP_Suitability_Score`| Float | $0.0 - 100.0$ | Physical site suitability (slope, road, zoning) |
| `Suitability_Tier` | Categorical | Tiers | `Highly Suitable`, `Suitable`, `Moderately Suitable` |
| `AIPS` | Float | $0.0 - 100.0$ | Adaptive Infrastructure Planning Score |
| `Robustness_Category` | Categorical | Tiers | `Very Robust`, `Robust`, `Moderately Robust`, `Sensitive` |

---

## 4. Machine Learning Feature Set & Targets

### Feature Matrix ($X \in \mathbb{R}^{648 \times 10}$):
1. `Population` (Continuous): Resident count
2. `Population_Density` (Continuous): Density per $\text{km}^2$
3. `Elderly` (Continuous): Geriatric residents (60+)
4. `Children` (Continuous): Pediatric residents (0-6)
5. `Households` (Continuous): Household estimate
6. `Vuln_Ratio` (Continuous): `(Elderly + Children) / Population`
7. `Nearest_Facility_Distance` (Continuous): Distance to primary post (km)
8. `Nearest_Hospital_Distance` (Continuous): Distance to secondary hospital (km)
9. `Healthcare_Facilities` (Integer): Existing clinics in ward
10. `Beds_per_1000` (Continuous): Inpatient beds per 1,000 residents

### Prediction Targets:
* **Classification Target ($y_{\text{clf}}$):** `Priority_Category` $\in \{\text{Low}, \text{Moderate}, \text{High}, \text{Critical}\}$
* **Regression Target ($y_{\text{reg}}$):** `Gap_Score` $\in [0.0, 100.0]$
* **Group Split Variable:** `City_Key` $\in \{\text{chennai}, \text{coimbatore}, \text{bengaluru}, \text{hyderabad}\}$
