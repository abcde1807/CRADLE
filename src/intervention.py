"""
CRADLE Intervention Recommendation Module
Rule-based planning recommendation engine that maps identified healthcare deficits
to specific policy interventions and facility types.
"""

from typing import Dict, Any, List
import pandas as pd

import config


class InterventionEngine:
    """
    Generates tailored healthcare infrastructure recommendations for wards and candidate sites
    based on gap severity, demographic demand, and dominant constraint type.
    """

    INTERVENTIONS = [
        "Construct New Facility",
        "Expand Existing Facility",
        "Increase Facility Capacity",
        "Improve Accessibility",
        "No Immediate Intervention",
    ]

    @classmethod
    def recommend_ward_intervention(cls, ward_row: pd.Series) -> Dict[str, Any]:
        """
        Determines the optimal policy intervention and recommended facility tier
        for an individual ward based on gap indicators.
        """
        gap_score = ward_row.get("Gap_Score", 0)
        priority = ward_row.get("Priority_Category", "Low")
        facilities = ward_row.get("Healthcare_Facilities", 0)
        beds_k = ward_row.get("Beds_per_1000", 0)
        dist_fac = ward_row.get("Nearest_Facility_Distance", 0)
        dist_hosp = ward_row.get("Nearest_Hospital_Distance", 0)
        pop = ward_row.get("Population", 0)

        # Baseline: Well served
        if gap_score < 25.0:
            return {
                "Intervention": "No Immediate Intervention",
                "Facility_Type": "None",
                "Estimated_Beds": 0,
                "Estimated_Cost_Crores": 0.0,
                "Rationale": "Ward maintains adequate healthcare capacity and spatial accessibility within standards.",
            }

        # Moderate Gap (25 - 50)
        if gap_score < 50.0:
            if facilities == 0 or dist_fac > 2.0:
                return {
                    "Intervention": "Construct New Facility",
                    "Facility_Type": "UPHC",
                    "Estimated_Beds": 10,
                    "Estimated_Cost_Crores": config.FACILITY_TYPES["UPHC"]["cost_crores"],
                    "Rationale": "Establish an Urban Primary Health Centre (UPHC) to close neighborhood walking distance deficit.",
                }
            else:
                return {
                    "Intervention": "Increase Facility Capacity",
                    "Facility_Type": "UPHC Upgrade",
                    "Estimated_Beds": 15,
                    "Estimated_Cost_Crores": 1.5,
                    "Rationale": "Add maternal/diagnostic beds and extended OPD hours to existing primary health post.",
                }

        # High Gap (50 - 75)
        if gap_score < 75.0:
            if facilities > 0 and beds_k < 1.0:
                return {
                    "Intervention": "Expand Existing Facility",
                    "Facility_Type": "CHC",
                    "Estimated_Beds": 35,
                    "Estimated_Cost_Crores": config.FACILITY_TYPES["CHC"]["cost_crores"],
                    "Rationale": "Upgrade existing primary center into a 35-bed Community Health Centre with 24x7 emergency response.",
                }
            elif dist_hosp > 4.0:
                return {
                    "Intervention": "Construct New Facility",
                    "Facility_Type": "CHC",
                    "Estimated_Beds": 50,
                    "Estimated_Cost_Crores": 10.0,
                    "Rationale": "Construct a new Community Health Centre to bridge the 4+ km secondary hospital access void.",
                }
            else:
                return {
                    "Intervention": "Improve Accessibility",
                    "Facility_Type": "Emergency Transit Hub / Mobile Clinic",
                    "Estimated_Beds": 0,
                    "Estimated_Cost_Crores": 2.0,
                    "Rationale": "Deploy dedicated emergency transit feeder corridors and mobile diagnostic units to improve connectivity.",
                }

        # Critical Gap (75 - 100)
        if pop > 45000 or dist_hosp > 5.0:
            return {
                "Intervention": "Construct New Facility",
                "Facility_Type": "Government Hospital",
                "Estimated_Beds": 200,
                "Estimated_Cost_Crores": config.FACILITY_TYPES["Government Hospital"]["cost_crores"],
                "Rationale": "Urgent priority: Construct a 200-bed secondary Government Hospital with trauma, pediatric, and intensive care.",
            }
        else:
            return {
                "Intervention": "Construct New Facility",
                "Facility_Type": "CHC",
                "Estimated_Beds": 60,
                "Estimated_Cost_Crores": 12.0,
                "Rationale": "Urgent priority: Construct a high-capacity 60-bed Community Health Centre to remediate severe healthcare desert conditions.",
            }

    @classmethod
    def recommend_candidate_intervention(cls, candidate_row: pd.Series) -> Dict[str, Any]:
        """
        Determines the recommended intervention configuration for a selected candidate site.
        """
        cand_score = candidate_row.get("Candidate_Score", 0)
        gap_score = candidate_row.get("Gap_Score", 0)
        pop_cov = candidate_row.get("Population_Covered", 0)

        if cand_score >= 75.0 or gap_score >= 75.0:
            fac_type = "Government Hospital"
            beds = 150
            cost = config.FACILITY_TYPES[fac_type]["cost_crores"]
            tier = "Tier 1 Priority - Major Facility Construction"
        elif cand_score >= 60.0:
            fac_type = "CHC"
            beds = 40
            cost = config.FACILITY_TYPES[fac_type]["cost_crores"]
            tier = "Tier 2 Priority - Community Health Centre"
        else:
            fac_type = "UPHC"
            beds = 15
            cost = config.FACILITY_TYPES[fac_type]["cost_crores"]
            tier = "Tier 3 Priority - Urban Primary Health Clinic"

        return {
            "Recommendation_Tier": tier,
            "Recommended_Facility_Type": fac_type,
            "Target_Bed_Capacity": beds,
            "Estimated_Capital_Expenditure_Cr": cost,
            "Estimated_Population_Served": pop_cov,
        }
