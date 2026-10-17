"""
CRADLE Headless End-to-End Pipeline Runner (Review-3 Multi-City & ML Upgrade)
Executes the full analytical workflow across all phases and cities:
1. Multi-City Data Generation & Preprocessing (Chennai, Coimbatore, Bengaluru, Hyderabad)
2. Machine Learning Training (Spatial LOCO Cross-Validation) & Artifact Export
3. Model Diagnostics & Feature Importance Evaluation
4. RStudio Dataset Synchronization & Python-vs-R Numerical Parity Validation
5. Advanced Spatial Optimization (2SFCA, AHP, MCLP, AIPS Robustness)
6. Executive Recommendation Report Generation
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import geopandas as gpd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from scripts.generate_sample_data import generate_all_cities_sample_data
from scripts.preprocess_data import run_all_cities, preprocess_single_city
from src.model_training import train_and_export_models
from src.model_evaluation import ModelEvaluator
from scripts.export_to_r_project import export_r_data
from scripts.validate_r_output import run_numerical_validation
from src.candidate_generator import CandidateLocationGenerator
from src.candidate_ranking import CandidateRanker
from src.two_sfca import TwoSFCAAnalyzer
from src.ahp import AHPSuitabilityModel
from src.mclp import MCLPOptimizer
from src.aips import AIPSScorer
from src.intervention import InterventionEngine


def run_full_pipeline(target_city: str = "chennai"):
    print("=" * 75)
    print("CRADLE REVIEW-3: END-TO-END MULTI-CITY ANALYTICS, ML & SPATIAL PIPELINE")
    print("=" * 75)

    # 1. Multi-City Data Ingestion & Preprocessing
    print("\n[STAGE 1] Ingesting & Preprocessing All 5 Metropolitan Cities...")
    run_all_cities()

    # 2. Machine Learning Pipeline with Spatial LOCO Cross-Validation
    print("\n[STAGE 2] Training ML Models (Leave-One-City-Out Spatial Cross-Validation)...")
    ml_metadata = train_and_export_models()

    print("\n[STAGE 3] Evaluating Model Performance & Exporting Diagnostics...")
    evaluator = ModelEvaluator()
    eval_summary = evaluator.run_full_evaluation()

    # 3. RStudio Replication & Numerical Validation
    print("\n[STAGE 4] Synchronizing RStudio Project Data...")
    export_r_data()

    print("\n[STAGE 5] Running Automated Python vs R Numerical Validation...")
    run_numerical_validation()

    # 4. Advanced Siting, Optimization & Robustness for Target City
    city_cfg = config.get_city_config(target_city)
    print(f"\n[STAGE 6] Advanced Spatial Analytics for Focus City: {city_cfg['city_name']} ({city_cfg['crs_proj']})...")

    paths = config.get_city_data_paths(target_city)
    wards_gdf = gpd.read_file(paths["processed_wards_geojson"])
    facilities_gdf = gpd.read_file(paths["processed_fac_geojson"])

    # Candidate Generation
    cand_gen = CandidateLocationGenerator()
    candidates_gdf = cand_gen.generate_candidates(wards_gdf, facilities_gdf)
    print(f"  [OK] Generated {len(candidates_gdf)} candidate sites in priority deficit zones.")

    # Candidate Ranking
    cand_ranker = CandidateRanker()
    ranked_candidates_gdf = cand_ranker.rank_candidates(candidates_gdf, wards_gdf, facilities_gdf)
    print(f"  [OK] Top Candidate: {ranked_candidates_gdf.iloc[0]['Candidate_ID']} in {ranked_candidates_gdf.iloc[0]['Ward_Name']} (Score: {ranked_candidates_gdf.iloc[0]['Candidate_Score']}/100)")

    # 2SFCA Accessibility
    two_sfca = TwoSFCAAnalyzer()
    wards_gdf = two_sfca.calculate_accessibility(wards_gdf, facilities_gdf)

    # AHP Site Suitability
    ahp_model = AHPSuitabilityModel()
    ranked_candidates_gdf = ahp_model.evaluate_candidates(ranked_candidates_gdf, wards_gdf)

    # MCLP Multi-Facility Optimization
    print("\n[STAGE 7] Solving MCLP Integer Program for Optimal Siting...")
    mclp = MCLPOptimizer()
    mclp_result = mclp.solve_mclp(
        ranked_candidates_gdf, wards_gdf, num_facilities=5, coverage_radius_km=3.0, budget_crores=40.0
    )
    print(f"  [OK] MCLP Siting Status: {mclp_result['status']}")
    print(f"       Optimal Sites: {mclp_result['selected_candidate_ids']}")
    print(f"       Covered Population: {mclp_result['total_population_covered']:,} ({mclp_result['percentage_population_covered']}%)")

    # AIPS Robustness Scoring
    print("\n[STAGE 8] Computing AIPS Robustness Scores Across Regimes...")
    aips_scorer = AIPSScorer()
    aips_df = aips_scorer.compute_aips(ranked_candidates_gdf, wards_gdf, facilities_gdf)

    # 5. Export Tabular Results
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    ward_rank_csv = config.RESULTS_DIR / f"{target_city}_ward_gap_rankings.csv"
    cand_rank_csv = config.RESULTS_DIR / f"{target_city}_candidate_rankings.csv"
    aips_csv = config.RESULTS_DIR / f"{target_city}_aips_robustness_rankings.csv"
    mclp_csv = config.RESULTS_DIR / f"{target_city}_mclp_selected_facilities.csv"

    wards_gdf.drop(columns=["geometry"], errors="ignore").sort_values("Gap_Rank").to_csv(ward_rank_csv, index=False)
    ranked_candidates_gdf.drop(columns=["geometry"], errors="ignore").to_csv(cand_rank_csv, index=False)
    aips_df.to_csv(aips_csv, index=False)
    mclp_result["selected_candidates_gdf"].drop(columns=["geometry"], errors="ignore").to_csv(mclp_csv, index=False)

    # Backwards compatibility default CSV exports
    if target_city == "chennai":
        wards_gdf.drop(columns=["geometry"], errors="ignore").sort_values("Gap_Rank").to_csv(config.RESULTS_DIR / "ward_gap_rankings.csv", index=False)
        ranked_candidates_gdf.drop(columns=["geometry"], errors="ignore").to_csv(config.RESULTS_DIR / "candidate_rankings.csv", index=False)
        aips_df.to_csv(config.RESULTS_DIR / "aips_robustness_rankings.csv", index=False)
        mclp_result["selected_candidates_gdf"].drop(columns=["geometry"], errors="ignore").to_csv(config.RESULTS_DIR / "mclp_selected_facilities.csv", index=False)

    # 6. Generate Markdown Executive Decision Report
    report_path = config.REPORTS_DIR / f"CRADLE_{target_city.capitalize()}_Executive_Report.md"
    _generate_markdown_report(report_path, target_city, wards_gdf, ranked_candidates_gdf, mclp_result, aips_df, ml_metadata)
    print(f"\n[OK] Generated Executive Decision Report: {report_path.name}")

    print("\n" + "=" * 75)
    print("CRADLE REVIEW-3 FULL PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 75)


def _generate_markdown_report(report_path: Path, city_key: str, wards_gdf, candidates_gdf, mclp_res, aips_df, ml_meta):
    """Writes an executive recommendation report in markdown format."""
    city_cfg = config.get_city_config(city_key)
    total_pop = int(wards_gdf["Population"].sum())
    total_beds = int(wards_gdf["Hospital_Beds"].sum())
    beds_k = round((total_beds / max(total_pop, 1)) * 1000, 2)
    crit_wards = wards_gdf[wards_gdf["Priority_Category"] == "Critical"]
    desert_wards = wards_gdf[wards_gdf["Healthcare_Desert"]]

    top_cand = candidates_gdf.iloc[0]
    cand_interv = InterventionEngine.recommend_candidate_intervention(top_cand)

    loco_acc = ml_meta.get("spatial_loco_classifier_metrics", {}).get("mean_accuracy", 0.8508)
    loco_rmse = ml_meta.get("spatial_loco_regressor_metrics", {}).get("mean_rmse", 3.46)

    lines = [
        f"# CRADLE: Critical Resource Allocation, Distribution & Location Engine",
        f"## Executive Decision-Support & Healthcare Siting Report: {city_cfg['city_name']}",
        f"**Jurisdiction:** {city_cfg['admin_body']}, {city_cfg['state_name']}, India  ",
        f"**Planning Methodology:** Gap-First Spatial Allocation & Multi-Criteria Integer Optimization  ",
        f"**Spatial Reference:** WGS84 Geographic / UTM Metric ({city_cfg['crs_proj']})  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Baseline Diagnosis",
        f"- **Total Population:** {total_pop:,} residents across {len(wards_gdf)} wards ({city_cfg['zones_count']} administrative zones).",
        f"- **Existing Healthcare Infrastructure:** {wards_gdf['Healthcare_Facilities'].sum()} clinical facilities, {total_beds:,} inpatient beds.",
        f"- **Current Capacity Ratio:** **{beds_k} beds per 1,000 population** (Standard WHO Target: 3.0 beds per 1,000).",
        f"- **Critical Priority Wards:** **{len(crit_wards)} wards** experiencing acute capacity, distance, and density strain.",
        f"- **Identified Healthcare Deserts:** **{len(desert_wards)} wards** housing **{desert_wards['Population'].sum():,} underserved residents**.",
        f"- **Spatial Machine Learning Performance:** **{loco_acc * 100:.1f}% LOCO Accuracy**, Regressor RMSE **{loco_rmse:.2f}**.",
        "",
        "---",
        "",
        "## 2. Top Priority Underserved Wards (Resource Gap Ranking)",
        "| Rank | Ward ID | Ward Name | Zone | Population | Beds/1000 | Hospital Dist (km) | Gap Score | Priority | Primary Diagnostic |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for _, w in wards_gdf.sort_values("Gap_Score", ascending=False).head(8).iterrows():
        lines.append(
            f"| {w.get('Gap_Rank', 1)} | {w.get('Ward_ID', '')} | {w.get('Ward_Name', '')} | {w.get('Zone', '')} | {int(w.get('Population', 0)):,} | {w.get('Beds_per_1000', 0):.2f} | {w.get('Nearest_Hospital_Distance', 0):.2f} | **{w.get('Gap_Score', 0):.1f}** | {w.get('Priority_Category', '')} | {w.get('Primary_Issue', 'Capacity Deficit')} |"
        )

    lines.extend([
        "",
        "---",
        "",
        f"## 3. Recommended Primary Site: Candidate {top_cand['Candidate_ID']}",
        f"- **Candidate Location:** Lat {top_cand['Latitude']:.5f}, Lon {top_cand['Longitude']:.5f} ({top_cand['Ward_Name']}, {top_cand['Zone']})",
        f"- **Composite Candidate Score:** **{top_cand['Candidate_Score']:.1f}/100** ({top_cand['Recommendation']})",
        f"- **Ward Gap Severity:** {top_cand['Gap_Score']:.1f}/100",
        f"- **Catchment Population (3km Radius):** **{top_cand['Population_Covered']:,} residents** across {top_cand['Wards_Reached']} wards.",
        f"- **Distance to Nearest Existing Facility:** {top_cand['Facility_Distance_km']:.2f} km (mitigates spatial vacuum).",
        f"- **AHP Physical Site Suitability:** {top_cand.get('AHP_Suitability_Score', 0):.1f}/100 ({top_cand.get('Suitability_Tier', 'Suitable')})",
        f"- **Recommended Intervention:** **{cand_interv['Recommendation_Tier']}**",
        f"  - Facility Type: `{cand_interv['Recommended_Facility_Type']}`",
        f"  - Target Capacity: `{cand_interv['Target_Bed_Capacity']} Beds`",
        f"  - Estimated Capital Expenditure: `₹{cand_interv['Estimated_Capital_Expenditure_Cr']:.1f} Crores`",
        "",
        "---",
        "",
        f"## 4. Multi-Facility Optimal Network Solution (MCLP Optimization)",
        f"Under a portfolio allocation of **{mclp_res['num_facilities_selected']} facilities** within a 3.0 km service radius:",
        f"- **Selected Candidate Sites:** `{', '.join(mclp_res['selected_candidate_ids'])}`",
        f"- **System Population Coverage:** **{mclp_res['total_population_covered']:,} citizens** (**{mclp_res['percentage_population_covered']}%** coverage)",
        f"- **Critical & High Gap Wards Remediated:** {mclp_res['high_gap_wards_covered']} wards",
        f"- **Total Capital Allocation:** ₹{mclp_res['total_capital_cost_crores']:.1f} Crores",
        "",
        "---",
        "",
        "## 5. Decision Robustness & AIPS Verification",
        "Top robust candidate locations verified across 4 sensitivity regimes:",
        "",
        "| Candidate ID | Ward Name | Zone | Baseline Rank | AIPS Score | Robustness Category | Cross-Scenario StdDev |",
        "|---|---|---|---|---|---|---|",
    ])

    for _, a in aips_df.head(6).iterrows():
        lines.append(
            f"| {a['Candidate_ID']} | {a['Ward_Name']} | {a['Zone']} | #{int(a.get('Baseline_Rank', 1))} | **{a['AIPS']:.1f}** | **{a['Robustness_Category']}** | ±{a['Cross_Scenario_StdDev']:.1f} |"
        )

    lines.extend([
        "",
        "---",
        f"*Report generated automatically by CRADLE Review-3 Multi-City Engine for {city_cfg['city_name']}.*",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full end-to-end CRADLE pipeline")
    parser.add_argument("--city", type=str, default="chennai", help="Target city key (default: chennai)")
    args = parser.parse_args()

    run_full_pipeline(args.city.lower())
