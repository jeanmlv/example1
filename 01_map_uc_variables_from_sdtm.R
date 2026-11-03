# ============================================================
# FIGARO UC301 - SDTM VARIABLE MAPPING / CANDIDATE SCANNER
# ============================================================
# Purpose:
#   1) Inventory all XPT datasets in the SDTM folder.
#   2) Build searchable metadata from TESTCD/TEST fields and SUPP QNAM/QLABEL.
#   3) Compare that metadata with the 37 UC variables of interest.
#   4) Merge the automated candidates with a curated mapping configuration.
#
# IMPORTANT:
#   Automated text matching is a discovery aid, NOT a replacement for
#   clinical/programming review. Derived endpoints and estimand variables
#   must not be created solely because component data are present.
# ============================================================

suppressPackageStartupMessages({
  library(haven)
  library(dplyr)
  library(purrr)
  library(stringr)
  library(tidyr)
  library(readr)
  library(tibble)
})

# ----------------------------
# CONFIGURATION
# ----------------------------
sdtm_dir <- "/domino/datasets/local/clinical-trial-data/SHP647UC301-FIGARO-UC-1/clinical/rawdata/shp647_301"
# Change if your Domino path differs.

# Output folder in Domino workspace.
# /mnt is usually writable, but this will fall back to the working directory.
output_dir <- "/mnt"
if (!dir.exists(output_dir) || file.access(output_dir, 2) != 0) {
  output_dir <- file.path(getwd(), "figaro_uc301_mapping_output")
}
dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

# Optional curated configuration.
# The scanner works even when this file is absent.
config_candidates <- c(
  "00_figaro_uc301_mapping_config.csv",
  "/mnt/00_figaro_uc301_mapping_config.csv",
  file.path(getwd(), "00_figaro_uc301_mapping_config.csv")
)
mapping_config_file <- config_candidates[file.exists(config_candidates)][1]
if (length(mapping_config_file) == 0 || is.na(mapping_config_file)) {
  mapping_config_file <- NA_character_
}

# ----------------------------
# 37 VARIABLES OF INTEREST
# ----------------------------
voi <- tribble(
  ~PARAMCD, ~DESCRIPTION,
  "MAYO", "Mayo Score",
  "ENSCORE", "Endoscopy Final Score",
  "RBSCORE", "Rectal Bleeding Score",
  "SFSCORE", "Stool Frequency Score",
  "ENCSCORE", "Endoscopy Central Score (Primary Reader)",
  "ENLSCORE", "Endoscopy Local Score",
  "UCEISP", "Total UCEIS Score (Primary ICE Approach)",
  "BLEEDP", "Bleeding (Primary ICE Approach)",
  "EROSP", "Erosions and Ulcers (Primary ICE Approach)",
  "VASCP", "Vascular Pattern (Primary ICE Approach)",
  "CRESPP", "Clin Resp (Primary Estimand Approach)",
  "HEHL", "Histo-Endo Mucosal Heal",
  "HIHL", "Histo Healing",
  "ENHLP", "Endoscopic Healing (Primary Estimand Approach)",
  "CREMP", "Clin Remiss (Primary Estimand Approach)",
  "PMRESPP", "Partial Mayo Resp (Primary ICE Approach)",
  "ARCHCH", "Architectural Change (Grade 0)",
  "CHRIINF", "Chronic Inflammatory Infiltrate (Grade 1)",
  "EOS", "Eosinophils (10^9/L)",
  "NEUTLP", "Neutrophils Lamina Propria (Grade 2B)",
  "NEUTEP", "Neutrophils Epithelium (Grade 3)",
  "CRYPTDES", "Crypt Destruction (Grade 4)",
  "ULCER", "Erosion or Ulceration (Grade 5)",
  "CRPP", "C Reactive Protein (mg/L) (Primary ICE Approach)",
  "CALPPP", "Fecal Calprotectin (mg/kg) (Primary ICE Approach)",
  "CORTBL", "Induction Baseline Corticosteroid Use",
  "IBDQTOT", "IBDQ Total Score",
  "PGSCORE", "Physician Global Assessment Score",
  "MOTEST", "Modified Mayo Score",
  "IBREMP", "IBDQ Remission (Primary Estimand Approach)",
  "HEHLP", "Histo-Endo Mucosal Heal (Primary Estimand Approach)",
  "ENNRMP", "Endoscopic Normalization (Primary Estimand Approach)",
  "NANCYHI", "Nancy Histological Index",
  "RHI", "Robarts Histopathology Index",
  "GBTOT", "Geboes total score",
  "GBHI", "Geboes high activity subscore",
  "GBLO", "Geboes low activity subscore"
)

# Extra search phrases improve candidate discovery.
aliases <- tribble(
  ~PARAMCD, ~ALIAS,
  "MAYO", "total mayo",
  "ENSCORE", "endoscopy outcome",
  "RBSCORE", "rectal bleeding",
  "SFSCORE", "stool frequency",
  "ENCSCORE", "central read endoscopy",
  "ENLSCORE", "site entered endoscopy",
  "UCEISP", "uceis",
  "BLEEDP", "bleeding",
  "EROSP", "erosion ulcer",
  "VASCP", "vascular pattern",
  "CRESPP", "clinical response responder",
  "HEHL", "histo endo mucosal heal",
  "HIHL", "histo healing",
  "ENHLP", "endoscopic healing",
  "CREMP", "clinical remission",
  "PMRESPP", "partial mayo response",
  "ARCHCH", "architectural change",
  "CHRIINF", "chronic inflammatory infiltrate",
  "EOS", "eosinophils",
  "NEUTLP", "lamina propria neutrophils",
  "NEUTEP", "neutrophils epithelium",
  "CRYPTDES", "crypt destruction",
  "ULCER", "erosion ulceration",
  "CRPP", "c reactive protein crp",
  "CALPPP", "fecal calprotectin calpro",
  "CORTBL", "corticosteroid",
  "IBDQTOT", "ibdq",
  "PGSCORE", "physician global assessment",
  "MOTEST", "modified mayo",
  "IBREMP", "ibdq remission",
  "HEHLP", "histo endo mucosal heal",
  "ENNRMP", "endoscopic normalization",
  "NANCYHI", "nancy histological index",
  "RHI", "robarts histopathology index",
  "GBTOT", "total geboes",
  "GBHI", "geboes high activity",
  "GBLO", "geboes low activity"
)

normalize_text <- function(x) {
  x %>%
    as.character() %>%
    str_to_lower() %>%
    str_replace_all("[^a-z0-9]+", " ") %>%
    str_squish()
}

# ----------------------------
# READ SDTM FILES
# ----------------------------
xpt_files <- list.files(sdtm_dir, pattern = "\\.xpt$", full.names = TRUE, ignore.case = TRUE)
if (length(xpt_files) == 0) stop("No XPT files found in: ", sdtm_dir)

safe_read_xpt <- function(path) {
  tryCatch(read_xpt(path), error = function(e) {
    warning("Could not read ", basename(path), ": ", conditionMessage(e))
    NULL
  })
}

sdtm <- set_names(map(xpt_files, safe_read_xpt), tools::file_path_sans_ext(basename(xpt_files)))
sdtm <- compact(sdtm)

inventory <- imap_dfr(sdtm, function(df, nm) {
  tibble(
    DATASET = nm,
    N_ROWS = nrow(df),
    N_COLS = ncol(df),
    VARIABLES = paste(names(df), collapse = " | ")
  )
})
write_csv(inventory, file.path(output_dir, "01_sdtm_inventory.csv"), na = "")

# ----------------------------
# BUILD SEARCHABLE METADATA
# ----------------------------
# Standard Findings classes usually expose --TESTCD/--TEST.
# SUPP-- domains use QNAM/QLABEL/QVAL.

extract_metadata <- function(df, dataset) {
  nms <- names(df)
  out <- list()

  testcd_vars <- nms[str_detect(nms, "TESTCD$")]
  for (tc in testcd_vars) {
    prefix <- str_remove(tc, "TESTCD$")
    test_var <- paste0(prefix, "TEST")
    if (test_var %in% nms) {
      tmp <- df %>%
        transmute(
          DATASET = dataset,
          CODE_VAR = tc,
          CODE = as.character(.data[[tc]]),
          LABEL_VAR = test_var,
          LABEL = as.character(.data[[test_var]])
        ) %>%
        filter(!is.na(CODE) | !is.na(LABEL)) %>%
        distinct()
      out[[length(out) + 1]] <- tmp
    }
  }

  if (all(c("QNAM", "QLABEL") %in% nms)) {
    tmp <- df %>%
      transmute(
        DATASET = dataset,
        CODE_VAR = "QNAM",
        CODE = as.character(QNAM),
        LABEL_VAR = "QLABEL",
        LABEL = as.character(QLABEL)
      ) %>%
      filter(!is.na(CODE) | !is.na(LABEL)) %>%
      distinct()
    out[[length(out) + 1]] <- tmp
  }

  if (length(out) == 0) return(tibble())
  bind_rows(out)
}

metadata <- imap_dfr(sdtm, extract_metadata) %>%
  mutate(
    SEARCH_TEXT = normalize_text(paste(CODE, LABEL))
  )

write_csv(metadata, file.path(output_dir, "02_sdtm_test_metadata.csv"), na = "")

# ----------------------------
# AUTOMATIC CANDIDATE SEARCH
# ----------------------------
search_terms <- voi %>%
  left_join(aliases, by = "PARAMCD") %>%
  mutate(SEARCH_TERM = normalize_text(paste(DESCRIPTION, ALIAS)))

# Token overlap score. This is intentionally simple and transparent.
token_score <- function(term, candidate) {
  a <- unique(str_split(term, " ", simplify = FALSE)[[1]])
  b <- unique(str_split(candidate, " ", simplify = FALSE)[[1]])
  a <- a[nchar(a) >= 3]
  b <- b[nchar(b) >= 3]
  if (length(a) == 0 || length(b) == 0) return(0)
  length(intersect(a, b)) / length(a)
}

candidates <- pmap_dfr(search_terms, function(PARAMCD, DESCRIPTION, ALIAS, SEARCH_TERM) {
  if (nrow(metadata) == 0) return(tibble())
  scores <- map_dbl(metadata$SEARCH_TEXT, ~token_score(SEARCH_TERM, .x))
  metadata %>%
    mutate(
      PARAMCD = PARAMCD,
      DESCRIPTION = DESCRIPTION,
      SCORE = scores
    ) %>%
    filter(SCORE > 0) %>%
    arrange(desc(SCORE)) %>%
    slice_head(n = 12)
}) %>%
  select(PARAMCD, DESCRIPTION, SCORE, DATASET, CODE_VAR, CODE, LABEL_VAR, LABEL)

write_csv(candidates, file.path(output_dir, "03_mapping_candidates_automatic.csv"), na = "")

# ----------------------------
# CURATED MAPPING
# ----------------------------
if (file.exists(mapping_config_file)) {
  curated <- read_csv(mapping_config_file, show_col_types = FALSE)
  write_csv(curated, file.path(output_dir, "04_mapping_reviewed_current.csv"), na = "")

  summary <- curated %>%
    count(STATUS, name = "N_VARIABLES") %>%
    arrange(desc(N_VARIABLES))
  write_csv(summary, file.path(output_dir, "05_mapping_status_summary.csv"), na = "")

  cat("\nReviewed mapping status:\n")
  print(summary)
} else {
  warning("Curated mapping config not found: ", mapping_config_file)
}

cat("\nDone. Output folder: ", normalizePath(output_dir), "\n", sep = "")
