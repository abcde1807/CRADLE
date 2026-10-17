# ==============================================================================
# CRADLE R REPLICATION: 01_LOAD_DATA.R
# Loads multi-city ward boundaries, population censuses, and healthcare facilities.
# Uses 'sf', 'readr', and 'dplyr'.
# ==============================================================================

suppressPackageStartupMessages({
  if (!requireNamespace("sf", quietly = TRUE)) install.packages("sf")
  if (!requireNamespace("readr", quietly = TRUE)) install.packages("readr")
  if (!requireNamespace("dplyr", quietly = TRUE)) install.packages("dplyr")
  library(sf)
  library(readr)
  library(dplyr)
})

# Define data paths relative to RStudio project root
DATA_DIR <- file.path("data")

load_city_data <- function(city_key = "chennai") {
  city_key <- tolower(city_key)
  cat(sprintf("\n[R-CRADLE] Ingesting spatial data for city: %s\n", toupper(city_key)))
  
  wards_path <- file.path(DATA_DIR, sprintf("%s_wards.geojson", city_key))
  pop_path <- file.path(DATA_DIR, sprintf("%s_population.csv", city_key))
  fac_path <- file.path(DATA_DIR, sprintf("%s_healthcare_facilities.csv", city_key))
  
  if (!file.exists(wards_path)) {
    stop(sprintf("Missing wards GeoJSON: %s", wards_path))
  }
  
  # Load wards boundary sf object
  wards_sf <- sf::st_read(wards_path, quiet = TRUE)
  # Ensure WGS84 CRS
  wards_sf <- sf::st_transform(wards_sf, 4326)
  
  # Load population CSV
  pop_df <- readr::read_csv(pop_path, show_col_types = FALSE)
  
  # Load healthcare facilities CSV and convert to sf point geometry
  fac_df <- readr::read_csv(fac_path, show_col_types = FALSE)
  fac_sf <- sf::st_as_sf(fac_df, coords = c("Longitude", "Latitude"), crs = 4326)
  
  # Metric CRS lookup
  crs_metric <- ifelse(city_key %in% c("chennai", "hyderabad"), 32644, 32643)
  
  cat(sprintf("  -> Wards Loaded: %d polygons\n", nrow(wards_sf)))
  cat(sprintf("  -> Population Records: %d\n", nrow(pop_df)))
  cat(sprintf("  -> Facilities Loaded: %d points (Metric CRS: EPSG:%d)\n", nrow(fac_sf), crs_metric))
  
  return(list(
    city_key = city_key,
    crs_metric = crs_metric,
    wards = wards_sf,
    population = pop_df,
    facilities = fac_sf
  ))
}

# Example execution if run standalone
if (sys.nframe() == 0) {
  data_chennai <- load_city_data("chennai")
}
