# example1


# ============================================================
# VEGA - SDTM load-2388 | Full UC Variable Mapping + ARD
# ============================================================

library(dplyr)
library(tidyr)
library(readr)
library(stringr)
library(purrr)
library(tibble)

CONFIG <- list(
  study_id = "CNTO1959UCO2002_VEGA",

  input_dir = paste0(
    "/domino/datasets/local/clinical-trial-data/",
    "CNTO1959UCO2002-VEGA-WK50/load-2388/Data"
  ),

  output_dir = "/domino/vega_load2388_ard",

  output_dataset = "vega_load2388_sdtm_ard.csv",
  mapping_report = "vega_load2388_mapping.csv",
  qc_report = "vega_load2388_qc.csv"
)

# Compatibility with the existing script
study_id <- CONFIG$study_id
sdtm_root <- CONFIG$input_dir
output_dir <- CONFIG$output_dir

reviewed_mapping_file <- file.path(
  output_dir,
  "05_reviewed_mapping_template.csv"
)

dir.create(
  output_dir,
  recursive = TRUE,
  showWarnings = FALSE
)

if (!dir.exists(sdtm_root)) {
  stop("Input directory not found: ", sdtm_root)
}

if (!dir.exists(output_dir)) {
  stop("Could not create output directory: ", output_dir)
}

cat("Study:", study_id, "\n")
cat("Input:", sdtm_root, "\n")
cat("Output:", output_dir, "\n")
