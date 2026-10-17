# ==============================================================================
# CRADLE R REPLICATION: 03_GAP_ANALYZER.R
# Computes the 4-indicator Healthcare Gap Score (0-100) and priority tiers.
# Formula matches Python implementation within floating-point tolerance.
# ==============================================================================

suppressPackageStartupMessages({
  library(sf)
  library(dplyr)
})

calculate_gap_scores_r <- function(wards_sf, weights = NULL) {
  if (is.null(weights)) {
    weights <- list(
      pop_pressure = 0.30,
      capacity_deficit = 0.30,
      distance_gap = 0.25,
      facility_scarcity = 0.15
    )
  }
  
  gdf <- wards_sf
  
  # 1. Population Pressure (0 to 1)
  density_p95 <- as.numeric(quantile(gdf$Population_Density, 0.95, na.rm = TRUE))
  density_p95 <- max(density_p95, 1.0)
  norm_density <- pmin(pmax(gdf$Population_Density / density_p95, 0.0), 1.0)
  
  if ("Elderly" %in% names(gdf) && "Children" %in% names(gdf)) {
    vuln_ratio <- pmin(pmax((gdf$Elderly + gdf$Children) / pmax(gdf$Population, 1), 0.0), 1.0)
    pop_pressure <- pmin(pmax(0.7 * norm_density + 0.3 * vuln_ratio, 0.0), 1.0)
  } else {
    pop_pressure <- norm_density
  }
  
  # 2. Capacity Deficit (0 to 1) relative to WHO 3.0 beds/1,000 benchmark
  who_target <- 3.0
  capacity_deficit <- pmin(pmax(1.0 - (gdf$Beds_per_1000 / who_target), 0.0), 1.0)
  
  # 3. Distance Gap (0 to 1)
  norm_fac_dist <- pmin(pmax(gdf$Nearest_Facility_Distance / 2.5, 0.0), 1.0)
  norm_hosp_dist <- pmin(pmax(gdf$Nearest_Hospital_Distance / 5.0, 0.0), 1.0)
  distance_gap <- pmin(pmax(0.4 * norm_fac_dist + 0.6 * norm_hosp_dist, 0.0), 1.0)
  
  # 4. Facility Scarcity (0 to 1) relative to 1.5 facilities / 10,000 benchmark
  fac_per_10k <- (gdf$Healthcare_Facilities / pmax(gdf$Population, 1)) * 10000
  facility_scarcity <- pmin(pmax(1.0 - (fac_per_10k / 1.5), 0.0), 1.0)
  
  # Composite Healthcare Gap Score (0 to 100)
  raw_gap <- (
    weights$pop_pressure * pop_pressure +
    weights$capacity_deficit * capacity_deficit +
    weights$distance_gap * distance_gap +
    weights$facility_scarcity * facility_scarcity
  ) * 100.0
  
  gdf$Gap_Score_R <- round(pmin(pmax(raw_gap, 0.0), 100.0), 1)
  
  # Priority Category Classification (Matching Python classify_priority thresholds)
  gdf$Priority_Category_R <- case_when(
    gdf$Gap_Score_R >= 70.0 ~ "Critical",
    gdf$Gap_Score_R >= 50.0 ~ "High",
    gdf$Gap_Score_R >= 25.0 ~ "Moderate",
    TRUE                    ~ "Low"
  )
  
  return(gdf)
}
