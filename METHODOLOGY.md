# CRADLE Analytical Methodology & Mathematical Formulations

## 1. Core Philosophy: Gap-First Healthcare Facility Allocation

Conventional public infrastructure models typically follow a **Land-First Approach**:
$$\text{Available Vacant Land} \longrightarrow \text{Zoning \& Permitting} \longrightarrow \text{Facility Construction}$$

This approach frequently produces spatial misallocations in rapidly expanding Indian metropolises, concentrating state-of-the-art hospitals in wealthy commercial corridors or suburban peripheries while dense informal settlements and historic urban cores remain underserved.

**CRADLE inverts this paradigm through a Gap-First Spatial Allocation Framework:**

```text
Healthcare Demand & Demographics
      ↓
Resource Deficit Diagnosis
      ↓
4-Indicator Healthcare Gap Score (0 - 100)
      ↓
Identification of Priority Wards & Healthcare Deserts
      ↓
Candidate Site Generation in Deficit Voids (500m Grid)
      ↓
Multi-Criteria Candidate Ranking & Population Catchment
      ↓
Physical Site Suitability (AHP - Evaluated Separately from Need)
      ↓
Maximal Covering Optimization (MCLP Integer Program)
      ↓
Adaptive Infrastructure Planning Score (AIPS Robustness)
      ↓
Actionable Decision Support & Capital Budget Allocation
```

---

## 2. The 4-Indicator Healthcare Gap Score Formulation

For each municipal ward $i$, CRADLE calculates a composite Healthcare Gap Score ($0 - 100$) by synthesizing four normalized indicators ($[0, 1]$):

$$\text{Gap Score}_i = \left( w_p \cdot P_i + w_c \cdot C_i + w_d \cdot D_i + w_s \cdot S_i \right) \times 100$$

Subject to the weight normalization constraint:
$$\sum_{k \in \{p, c, d, s\}} w_k = 1.0 \quad (w_p = 0.30, \, w_c = 0.30, \, w_d = 0.25, \, w_s = 0.15)$$

### Component 1: Population Pressure ($P_i$, Default Weight 30%)
Combines localized density with demographic vulnerability (elderly and children):

$$P_i = \min\left(1.0, \, 0.70 \cdot \frac{\text{Density}_i}{\text{P95}(\text{Density})} + 0.30 \cdot \frac{\text{Elderly}_i + \text{Children}_i}{\text{Population}_i}\right)$$

### Component 2: Capacity Deficit ($C_i$, Default Weight 30%)
Evaluates ward inpatient bed availability relative to the World Health Organization (WHO) benchmark ($3.0$ beds per 1,000 residents):

$$C_i = \max\left(0.0, \, 1.0 - \frac{\text{Beds per 1000}_i}{3.0}\right)$$

### Component 3: Distance Gap ($D_i$, Default Weight 25%)
Measures physical travel impedance from the ward centroid to the nearest healthcare facility and secondary/tertiary hospital:

$$D_i = \min\left(1.0, \, 0.40 \cdot \frac{d_{\text{facility}, i}}{2.5\text{ km}} + 0.60 \cdot \frac{d_{\text{hospital}, i}}{5.0\text{ km}}\right)$$

### Component 4: Facility Scarcity ($S_i$, Default Weight 15%)
Measures the absence of localized primary health clinics against a baseline target of $1.5$ facilities per 10,000 residents:

$$S_i = \max\left(0.0, \, 1.0 - \frac{\left(\frac{\text{Facilities}_i}{\text{Population}_i} \times 10,000\right)}{1.5}\right)$$

### Priority Classification Tiers:
* **$\text{Gap Score} \ge 70.0$:** `Critical Priority` (Severe deficit; immediate capital intervention required)
* **$50.0 \le \text{Gap Score} < 70.0$:** `High Priority` (Underserved; requires secondary facility upgrade)
* **$25.0 \le \text{Gap Score} < 50.0$:** `Moderate Priority` (Minor deficit; outpatient post expansion)
* **$\text{Gap Score} < 25.0$:** `Low Priority` (Adequately resourced; baseline maintenance)

---

## 3. Healthcare Desert Detection & Severity Index

A ward $i$ is classified as a **Healthcare Desert** ($H_i = \text{True}$) if high overall need coincides with extreme physical isolation or acute capacity deprivation:

$$H_i = (\text{Gap Score}_i \ge 60.0) \land \left( d_{\text{hospital}, i} \ge 3.5\text{ km} \lor (\text{Beds per 1000}_i \le 1.0 \land \text{Facilities}_i \le 1) \right)$$

For desert wards, the **Desert Severity Index ($0 - 100$)** scales the degree of vulnerability:

$$\text{Severity}_i = \left( 0.45 \cdot \frac{\text{Gap}_i}{100} + 0.35 \cdot \min\left(1.0, \frac{d_{\text{hospital}, i}}{10.5\text{ km}}\right) + 0.20 \cdot \max\left(0.0, 1 - \frac{\text{Beds}_i}{3.0}\right) \right) \times 100$$

---

## 4. Facility Pressure Analysis (Gravity Catchment Model)

Patient allocation across facilities is modeled using a distance-decayed spatial gravity formulation. The probability $P_{ij}$ that residents of ward $i$ seek care at facility $j$ is:

$$P_{ij} = \frac{\left(\text{Capacity}_j\right)^\alpha \cdot \left(d_{ij}\right)^{-\beta}}{\sum_{k \in \mathcal{F}_i} \left(\text{Capacity}_k\right)^\alpha \cdot \left(d_{ik}\right)^{-\beta}}$$

* $\alpha = 0.8$ (Attractiveness scaling with facility size)
* $\beta = 1.5$ (Spatial distance-decay friction)
* $\mathcal{F}_i = \{j \mid d_{ij} \le 8.0\text{ km}\}$ (Maximum feasible travel radius)

Allocated population demand:
$$\text{Pop Served}_j = \sum_{i} P_{ij} \cdot \text{Population}_i$$

Facility Pressure Ratio:
$$\text{Pressure Ratio}_j = \frac{\text{Pop Served}_j}{\text{Beds}_j \times 333.3}$$
*(Classified as Critical $\ge 5.0$, High $\ge 2.5$, Moderate $\ge 1.0$, Low $< 1.0$)*.

---

## 5. Candidate Generation, Siting & Separation Principles

### Separation of Need vs. Feasibility
A foundational principle of CRADLE is the **strict mathematical separation of Healthcare Need (Gap Score) from Physical Site Suitability (AHP)**:
- **Need (Where is care required?):** Governed solely by demographics, disease vulnerability, and access deficits.
- **Suitability (Where can a building physically stand?):** Governed by land zoning, road proximity, slope, flood plains, and vacant parcel size.
- Conflating need and suitability in a single index obscures why a site was chosen and can lead planners to build in inappropriate areas simply because vacant land was cheap.

### Spatial Candidate Generation:
1. Target priority wards ($\text{Priority} \in \{\text{Critical}, \text{High}\}$).
2. Reproject to metric UTM coordinates (`EPSG:32644` / `EPSG:32643`).
3. Construct a $500\text{m} \times 500\text{m}$ orthogonal lattice grid within each ward polygon.
4. Apply an **exclusion buffer** of $600\text{m}$ around all existing healthcare facilities to prevent redundant spatial clustering.
5. Filter points strictly contained within the municipal ward boundaries.

### Candidate Ranking Score ($0 - 100$):
$$\text{Candidate Score}_k = 0.40 \cdot \text{Gap}_k + 0.30 \cdot \text{PopCov}_k + 0.20 \cdot \text{FacilityDist}_k + 0.10 \cdot \text{RoadProx}_k$$

---

## 6. Two-Step Floating Catchment Area (2SFCA) Accessibility

2SFCA measures spatial healthcare accessibility by accounting for both service supply (beds) and population demand through a two-step floating catchment:

### Step 1: Compute Provider-to-Population Ratio ($R_j$)
For each healthcare facility $j$:
$$R_j = \frac{S_j}{\sum_{k \in \{k \mid d_{kj} \le d_0\}} P_k \cdot f(d_{kj})}$$
Where $S_j$ is facility bed capacity, $P_k$ is population of ward $k$, $d_0 = 4.0\text{ km}$, and $f(d)$ is the gravity decay function:
$$f(d) = \left(\frac{\max(d, 0.5)}{d_0}\right)^{-\beta}$$

### Step 2: Sum Facility Ratios Accessible to Population ($A_i$)
For each ward $i$:
$$A_i = \sum_{j \in \{j \mid d_{ij} \le d_0\}} R_j \cdot f(d_{ij})$$

---

## 7. Maximal Covering Location Problem (MCLP) Formulation

Given candidate sites $J$ and demand wards $I$, MCLP maximizes the population covered within service radius $R_c = 3.0\text{ km}$ subject to building at most $p$ facilities within a total capital budget $B$:

$$\max_{x, y} \sum_{i \in I} w_i \cdot y_i$$

Subject to:
$$\sum_{j \in N_i} x_j \ge y_i \quad \forall i \in I$$
$$\sum_{j \in J} x_j = p$$
$$\sum_{j \in J} c_j \cdot x_j \le B$$
$$x_j \in \{0, 1\} \quad \forall j \in J, \quad y_i \in \{0, 1\} \quad \forall i \in I$$

Where:
* $w_i = \text{Population}_i \cdot (\text{Gap Score}_i / 100)$ (Demand weight favoring high-deficit populations)
* $N_i = \{j \in J \mid d_{ij} \le R_c\}$ (Candidate sites capable of covering ward $i$)
* $x_j = 1$ if candidate facility $j$ is constructed, $0$ otherwise
* $y_i = 1$ if ward $i$ is covered by at least one selected facility, $0$ otherwise
* $c_j$ is the capital cost of facility $j$ (typically ₹8 Cr for CHC, ₹25 Cr for Hospital)
* $B$ is the available municipal budget envelope

---

## 8. Adaptive Infrastructure Planning Score (AIPS) Robustness

To ensure siting decisions do not depend excessively on subjective weighting assumptions, CRADLE evaluates candidates across 4 distinct planning regimes:
1. **Regime 1: Balanced Policy** ($w = [0.30, 0.30, 0.25, 0.15]$)
2. **Regime 2: Population & Density Focus** ($w = [0.55, 0.20, 0.15, 0.10]$)
3. **Regime 3: Bed Capacity Focus** ($w = [0.15, 0.55, 0.15, 0.15]$)
4. **Regime 4: Spatial Distance Focus** ($w = [0.15, 0.15, 0.55, 0.15]$)

Let $r_{k, m}$ be the rank of candidate $k$ under regime $m$. The **AIPS Robustness Index** balances mean rank and rank volatility:

$$\text{AIPS}_k = \left( 0.70 \cdot \left(1.0 - \frac{\bar{r}_k - 1}{|J| - 1}\right) + 0.30 \cdot \left(1.0 - \frac{\sigma(r_k)}{\sigma_{\max}}\right) \right) \times 100$$

*(Classified as Very Robust $\ge 85.0$, Robust $\ge 70.0$, Moderately Robust $\ge 50.0$, Sensitive $< 50.0$)*.

---

## 9. Spatial Machine Learning & Leave-One-City-Out Rationale

### Why Random k-Fold Fails in Spatial Analytics:
Standard randomized $k$-fold cross-validation assigns randomly selected wards to training and validation sets. Due to **spatial autocorrelation** (Tobler's First Law: *"everything is related to everything else, but near things are more related than distant things"*), adjacent wards share unobserved spatial features (road corridors, economic clustering, demographic gradients). Random splitting causes severe data leakage, inflating test accuracy artificially while performing poorly in a new jurisdiction.

### Leave-One-City-Out (LOCO) Spatial Cross-Validation:
CRADLE groups data strictly by municipal jurisdiction $\text{City}_k$:
- Fold 1: Train on Chennai, Coimbatore, Hyderabad $\longrightarrow$ Test on **Bengaluru**
- Fold 2: Train on Coimbatore, Bengaluru, Hyderabad $\longrightarrow$ Test on **Chennai**
- Fold 3: Train on Chennai, Bengaluru, Hyderabad $\longrightarrow$ Test on **Coimbatore**
- Fold 4: Train on Chennai, Coimbatore, Bengaluru $\longrightarrow$ Test on **Hyderabad**

This guarantees that validation metrics measure genuine cross-metropolitan generalizability.
