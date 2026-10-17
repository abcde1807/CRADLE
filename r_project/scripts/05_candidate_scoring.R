# ==============================================================================
# CRADLE R REPLICATION: 05_CANDIDATE_SCORING.R
# Ranks candidate facility locations and evaluates population catchment coverage.
# ==============================================================================

suppressPackageStartupMessages({
  library(sf)
  library(dplyr)
})

rank_candidates_r <- function(wards_sf, facilities_sf, crs_metric = 32644) {
  # Select high/critical priority wards
  gap_col <- if ("Gap_Score_R" %in% names(wards_sf)) "Gap_Score_R" else "Gap_Score"
  priority_wards <- wards_sf %>% filter(.data[[gap_col]] >= 60.0)
  
  if (nrow(priority_wards) == 0) {
    priority_wards <- wards_sf %>% arrange(desc(.data[[gap_col]])) %>% head(10)
  }
  
  # Project to metric CRS
  wards_utm <- sf::st_transform(priority_wards, crs_metric)
  fac_utm <- sf::st_transform(facilities_sf, crs_metric)
  
  # Generate candidate points at priority ward centroids
  cand_points <- suppressWarnings(sf::st_centroid(wards_utm))
  
  # Compute distance from candidates to existing facilities
  dist_to_fac <- sf::st_distance(cand_points, fac_utm)
  min_dist_fac <- apply(dist_to_fac, 1, min) / 1000.0
  
  # Filter candidates with at least 500m buffer from existing facilities
  cand_points$Dist_To_Existing_km <- as.numeric(min_dist_fac)
  valid_cands <- cand_points %>% filter(Dist_To_Existing_km >= 0.5)
  
  if (nrow(valid_cands) == 0) {
    valid_cands <- cand_points
  }
  
  # Normalize components (0-1)
  max_gap <- max(valid_cands[[gap_col]], na.rm = TRUE)
  norm_gap <- valid_cands[[gap_col]] / max(max_gap, 1.0)
  
  max_pop <- max(valid_cands$Population, na.rm = TRUE)
  norm_pop <- valid_cands$Population / max(max_pop, 1.0)
  
  norm_dist <- pmin(valid_cands$Nearest_Hospital_Distance / 5.0, 1.0)
  norm_isolation <- pmin(valid_cands$Dist_To_Existing_km / 3.0, 1.0)
  
  # Composite Priority Siting Score (0-100)
  valid_cands$Siting_Score_R <- round((
    0.40 * norm_gap +
    0.30 * norm_pop +
    0.20 * norm_dist +
    0.10 * norm_isolation
  ) * 100.0, 1)
  
  ranked_cands <- valid_cands %>%
    arrange(desc(Siting_Score_R)) %>%
    mutate(Rank_R = row_number())
  
  return(sf::st_transform(ranked_cands, 4326))
}
