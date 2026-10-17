source("scripts/01_load_data.R")
source("scripts/02_preprocessing.R")
source("scripts/03_gap_analyzer.R")
source("scripts/04_healthcare_deserts.R")
source("scripts/05_candidate_scoring.R")

cat("=== Testing Step 1 & 2: Preprocessing Delhi ===\n")
p <- preprocess_city("delhi")

cat("\n=== Testing Step 3: Gap Analyzer ===\n")
g <- calculate_gap_scores_r(p$wards)
cat("Mean Gap Score:", round(mean(g$Gap_Score_R), 2), "/ 100\n")

cat("\n=== Testing Step 4: Desert Detection ===\n")
d <- detect_healthcare_deserts_r(g)
cat("Total Desert Wards:", sum(d$Healthcare_Desert_R), "\n")

cat("\n=== Testing Step 5: Candidate Site Ranking ===\n")
c <- rank_candidates_r(d, p$facilities, p$crs_metric)
cat("Total Candidate Sites Ranked:", nrow(c), "\n")
cat("Top Ranked Candidate Site in Ward:", c$Ward_Name[1], "with Score:", c$Siting_Score_R[1], "\n")

cat("\n[SUCCESS] Full R pipeline executed cleanly with 0 errors!\n")
