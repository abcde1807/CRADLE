# CRADLE Data Sources, Provenance & Ingestion Guide

## 1. Data Provenance & Academic Honesty Statement

To maintain complete academic and engineering integrity, CRADLE transparently declares:

> **All spatial boundaries, demographic profiles, and healthcare facility inventories currently packaged in `data/sample/` and `data/processed/` are SYNTHETIC DEVELOPMENT DATASETS calibrated to realistic 2024 municipal statistical abstracts.**

These datasets have been mathematically constructed to mirror the exact spatial bounds, zone structures, population magnitudes, facility density distributions, and bed capacities of the target Indian municipal corporations.

---

## 2. Municipal Alignment & Calibration References

| City | Municipal Corporation | Official Reference Report | Population Calibrated | Wards | Zones | Anchor Facilities Calibrated |
|---|---|---|---|---|---|---|
| **Chennai** | Greater Chennai Corporation (GCC) | GCC Public Health Department Statistical Handbook (2024) & Census of India | ~10.1 Million | 200 | 15 | RGGGH, Stanley, Kilpauk, Royapettah, Apollo Greams, MIOT |
| **Coimbatore** | Coimbatore City Municipal Corp (CCMC) | CCMC Annual Administrative Report & Health Profile (2024) | ~2.65 Million | 100 | 5 | CMCH, ESI Singanallur, PSG Peelamedu, KMCH, Ganga |
| **Bengaluru** | Bruhat Bengaluru Mahanagara Palike (BBMP) | BBMP Health Cadre Statistics & Karnataka State Health Dashboard (2024) | ~13.7 Million | 198 | 8 | Victoria, Bowring, KC General, Jayanagar, NIMHANS, Manipal |
| **Hyderabad** | Greater Hyderabad Municipal Corp (GHMC) | GHMC Public Health & Sanitation Statistical Abstract (2024) | ~11.0 Million | 150 | 6 | Osmania, Gandhi, NIMS, Fever Hospital, Yashoda, Apollo |

### Calibration Standards:
1. **Facility Sizing & Types:** Derived from the **Indian Public Health Standards (IPHS 2022 Guidelines)**:
   - Primary Health Centre (PHC): 4–10 beds, 2 doctors
   - Urban Primary Health Centre (UPHC): 6–15 beds, 3 doctors
   - Community Health Centre (CHC): 30–50 beds, 6 doctors
   - Government Hospital: 100–350 beds, 25 doctors
   - General / Teaching Hospital: 400–1,200 beds, 80+ doctors
2. **Age Distribution:** Derived from the **Sample Registration System (SRS) Statistical Report** (Children 0–6: ~14–20%, Elderly 60+: ~8–13%, Working Age: ~67–75%).
3. **Household Size:** Average 3.7 to 4.3 persons per household in metropolitan Indian corporations.

---

## 3. Production Ingestion Guide: Replacing Synthetic with Real Data

CRADLE is engineered with an **adapter-based architecture**. To switch from development data to live municipal production data, no Python code changes are required:

### Step 1: Prepare Municipal Input Files
Place your files in `data/raw/` using either GeoJSON or ESRI Shapefile format:

```text
data/raw/
├── {city_key}_wards.geojson      (or {city_key}_wards.shp)
├── {city_key}_population.csv
└── {city_key}_healthcare_facilities.csv
```

### Step 2: Ensure Expected Column Headers

#### A. Wards File (`{city}_wards.geojson`):
- `Ward_ID`: Integer identifier
- `Ward_Name`: Ward name string
- `Zone`: Zone name string
- `geometry`: Polygon / MultiPolygon in EPSG:4326

#### B. Population File (`{city}_population.csv`):
- `Ward_ID`: Integer identifier matching the wards file
- `Population`: Total resident population
- Optional: `Elderly`, `Children`, `Households`

#### C. Healthcare Facilities File (`{city}_healthcare_facilities.csv`):
- `Facility_ID`: String identifier (e.g., `FAC_001`)
- `Facility_Name`: Facility name string
- `Facility_Type`: `PHC`, `UPHC`, `CHC`, `Government Hospital`, `General Hospital`, `Multi-Speciality Hospital`, `Private Clinic`
- `Ownership`: `Public` or `Private`
- `Beds`: Inpatient bed count
- `Doctors`: Medical officer count
- `Latitude`: Decimal degrees (WGS84)
- `Longitude`: Decimal degrees (WGS84)

### Step 3: Run the Ingestion Pipeline
```bash
python scripts/preprocess_data.py --city {city_key}
```
The pipeline automatically:
1. Validates coordinate bounds and reprojects to the city's metric UTM zone.
2. Performs point-in-polygon spatial integration.
3. Computes Gap Scores, detects Healthcare Deserts, and analyzes Facility Strain.
4. Generates analysis-ready files in `data/processed/`.
