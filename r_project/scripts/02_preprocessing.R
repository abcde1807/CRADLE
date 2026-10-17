# ==============================================================================
# CRADLE R REPLICATION: 02_PREPROCESSING.R
# Spatial integration, demographic joins, facility density, and Euclidean distance.
# ==============================================================================

suppressPackageStartupMessages({
  library(sf)
  library(readr)
  library(dplyr)
})

source(file.path("scripts", "01_load_data.R"))

preprocess_city <- function(city_key = "chennai") {
  raw <- load_city_data(city_key)
  wards_sf <- raw$wards
  pop_df <- raw$population
  fac_sf <- raw$facilities
  crs_metric <- raw$crs_metric
  
  cat(sprintf("\n[R-CRADLE] Preprocessing and spatial integration for %s...\n", toupper(city_key)))
  
  # 1. Join population demographics
  # Normalize join column names
  if ("Ward_ID" %in% names(pop_df) && "Ward_ID" %in% names(wards_sf)) {
    wards_sf$Ward_ID <- as.integer(wards_sf$Ward_ID)
    # Avoid column name collision (.x / .y) by only selecting new columns from pop_df
    pop_cols <- c("Ward_ID", setdiff(names(pop_df), names(wards_sf)))
    merged_sf <- wards_sf %>% left_join(pop_df[, pop_cols], by = "Ward_ID")
  } else {
    merged_sf <- wards_sf
  }
  
  # 2. Project to city-specific metric CRS for accurate geodesic distances and areas
  wards_utm <- sf::st_transform(merged_sf, crs_metric)
  fac_utm <- sf::st_transform(fac_sf, crs_metric)
  
  # Calculate area in sq km
  areas_m2 <- as.numeric(sf::st_area(wards_utm))
  wards_utm$Area_sqkm <- round(areas_m2 / 1e6, 3)
  
  # Population density
  if ("Population" %in% names(wards_utm)) {
    wards_utm$Population_Density <- round(wards_utm$Population / pmax(wards_utm$Area_sqkm, 0.05), 1)
  }
  
  # 3. Spatial Join: Count facilities and beds located inside each ward polygon
  # Point in polygon
  pts_in_poly <- sf::st_join(fac_utm, wards_utm[, c("Ward_ID")], join = sf::st_intersects)
  
  fac_summary <- pts_in_poly %>%
    sf::st_drop_geometry() %>%
    group_by(Ward_ID) %>%
    summarise(
      Healthcare_Facilities = n(),
      Hospital_Beds = sum(Beds, na.rm = TRUE),
      .groups = "drop"
    )
  
  # Join back to wards
  wards_utm <- wards_utm %>%
    left_join(fac_summary, by = "Ward_ID") %>%
    mutate(
      Healthcare_Facilities = coalesce(Healthcare_Facilities, 0L),
      Hospital_Beds = coalesce(Hospital_Beds, 0L)
    )
  
  # Beds per 1,000 population
  wards_utm$Beds_per_1000 <- round((wards_utm$Hospital_Beds / pmax(wards_utm$Population, 1)) * 1000, 2)
  
  # 4. Nearest Facility & Nearest Hospital Distance Calculations
  ward_centroids <- suppressWarnings(sf::st_centroid(wards_utm))
  
  # Distance to nearest facility (any type)
  dist_matrix_all <- sf::st_distance(ward_centroids, fac_utm)
  min_dist_fac_km <- apply(dist_matrix_all, 1, min) / 1000.0
  wards_utm$Nearest_Facility_Distance <- round(as.numeric(min_dist_fac_km), 2)
  
  # Filter secondary/tertiary hospitals
  hospital_types <- c("General Hospital", "Government Hospital", "Multi-Speciality Hospital", "CHC")
  if ("Level" %in% names(fac_utm)) {
    hosp_utm <- fac_utm %>% filter(Facility_Type %in% hospital_types | Level >= 2)
  } else {
    hosp_utm <- fac_utm %>% filter(Facility_Type %in% hospital_types)
  }
  
  if (nrow(hosp_utm) > 0) {
    dist_matrix_hosp <- sf::st_distance(ward_centroids, hosp_utm)
    min_dist_hosp_km <- apply(dist_matrix_hosp, 1, min) / 1000.0
    wards_utm$Nearest_Hospital_Distance <- round(as.numeric(min_dist_hosp_km), 2)
  } else {
    wards_utm$Nearest_Hospital_Distance <- wards_utm$Nearest_Facility_Distance
  }
  
  # Transform back to WGS84 for GeoJSON export
  processed_wards <- sf::st_transform(wards_utm, 4326)
  
  cat(sprintf("  [OK] Preprocessing completed for %d wards.\n", nrow(processed_wards)))
  return(list(wards = processed_wards, facilities = fac_utm, crs_metric = crs_metric))
}

if (sys.nframe() == 0) {
  res <- preprocess_city("chennai")
}
