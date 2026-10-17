# ==============================================================================
# CRADLE R REPLICATION: 04_HEALTHCARE_DESERTS.R
# Detects urban healthcare deserts and calculates desert severity index (0-100).
# ==============================================================================

suppressPackageStartupMessages({
  library(sf)
  library(dplyr)
})

detect_healthcare_deserts_r <- function(wards_sf) {
  gdf <- wards_sf
  
  gap_col <- if ("Gap_Score_R" %in% names(gdf)) "Gap_Score_R" else "Gap_Score"
  
  # Threshold criteria
  cond_gap <- gdf[[gap_col]] >= 60.0
  cond_dist <- gdf$Nearest_Hospital_Distance >= 3.5
  cond_beds <- gdf$Beds_per_1000 <= 1.0
  cond_fac <- gdf$Healthcare_Facilities <= 1
  
  is_desert <- cond_gap & (cond_dist | (cond_beds & cond_fac))
  gdf$Healthcare_Desert_R <- is_desert
  
  # Severity calculation
  dist_factor <- pmin(pmax(gdf$Nearest_Hospital_Distance / 3.5, 1.0), 3.0) / 3.0
  bed_factor <- pmin(pmax(1.0 - (gdf$Beds_per_1000 / 3.0), 0.0), 1.0)
  gap_factor <- pmin(pmax(gdf[[gap_col]] / 100.0, 0.0), 1.0)
  
  raw_severity <- (0.45 * gap_factor + 0.35 * dist_factor + 0.20 * bed_factor) * 100.0
  gdf$Healthcare_Desert_Severity_R <- ifelse(is_desert, round(raw_severity, 1), 0.0)
  
  # Affected population
  gdf$Desert_Affected_Pop_R <- ifelse(is_desert, gdf$Population, 0)
  
  return(gdf)
}
