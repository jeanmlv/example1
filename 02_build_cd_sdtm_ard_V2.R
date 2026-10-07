# ============================================================
# 02_build_cd_sdtm_ard_V2.R
# GENERIC CROHN'S DISEASE SDTM -> GAP + TRACEABILITY + ARD
# ============================================================
#
# Companion to: map_cd_variables_from_sdtm.R
#
# V2 improvements:
#   1) MASTER VISIT GRID comes from SV whenever SV is available.
#      It no longer depends on the few variables already mapped.
#   2) Mapping classification uses evidence tiers instead of accepting only
#      exact code matches.
#   3) Strong text candidates are NOT automatically extracted merely because
#      SCORE is high. A generic semantic validator checks whether the target
#      description and SDTM label share meaningful clinical terms.
#   4) Ambiguous/derived-looking endpoints remain REVIEW_REQUIRED.
#   5) Manual reviewed overrides remain available per study.
#   6) Traceability records WHY each mapping was accepted.
#
# REQUIRED INPUTS:
#   - 03_mapping_candidates_automatic.csv
#   - 04_mapping_overview_best_candidate.csv
#   - SDTM XPT directory for the current CD study
#
# OUTPUTS:
#   01_gap_analysis.csv
#   02_traceability_summary.csv
#   03_traceability_long.csv
#   04_duplicate_review.csv
#   05_<study>_SDTM_based_ARD.csv
#   06_mapping_used_for_ARD.csv
#   07_mapping_review_queue.csv
#   08_mapping_decisions.csv
#   09_visit_grid_qc.csv
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

# ============================================================
# 1. CONFIGURATION
# ============================================================

study_id <- "CHANGE_ME"

sdtm_dir <- "/domino/datasets/local/CHANGE_ME/clinical/rawdata/CHANGE_ME"

candidate_mapping_files <- c(
  "03_mapping_candidates_automatic.csv",
  "/mnt/03_mapping_candidates_automatic.csv"
)

overview_files <- c(
  "04_mapping_overview_best_candidate.csv",
  "/mnt/04_mapping_overview_best_candidate.csv"
)

output_root <- "/mnt"
if (!dir.exists(output_root) || file.access(output_root, 2) != 0) {
  output_root <- getwd()
}

safe_study_id <- str_replace_all(study_id, "[^A-Za-z0-9_-]+", "_")
output_dir <- file.path(output_root, paste0(safe_study_id, "_cd_ard_output_V2"))
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

find_first <- function(x) {
  z <- x[file.exists(x)]
  if (length(z) == 0) NA_character_ else z[1]
}

candidate_file <- find_first(candidate_mapping_files)
overview_file  <- find_first(overview_files)

if (!dir.exists(sdtm_dir)) {
  stop("SDTM folder does not exist: ", sdtm_dir)
}
if (is.na(candidate_file)) stop("03_mapping_candidates_automatic.csv not found.")
if (is.na(overview_file)) stop("04_mapping_overview_best_candidate.csv not found.")

# ============================================================
# 2. READ SCANNER OUTPUTS
# ============================================================

candidates <- read_csv(candidate_file, show_col_types = FALSE) %>%
  mutate(
    PARAMCD = as.character(PARAMCD),
    DATASET = toupper(as.character(DATASET)),
    CODE = as.character(CODE),
    LABEL = as.character(LABEL)
  )

overview <- read_csv(overview_file, show_col_types = FALSE)

voi <- overview %>%
  select(PARAMCD, DESCRIPTION) %>%
  distinct()

# ============================================================
# 3. GENERIC SEMANTIC HELPERS
# ============================================================

norm <- function(x) {
  x %>%
    as.character() %>%
    str_to_lower() %>%
    str_replace_all("[^a-z0-9]+", " ") %>%
    str_squish()
}

# Generic stopwords / analysis qualifiers that should not dominate a match.
stop_tokens <- c(
  "primary","secondary","estimand","approach","score","total","final",
  "change","baseline","week","visit","index","value","result","results",
  "crohn","crohns","disease","activity","assessment","clinical",
  "patient","reported","outcome","subscore","status"
)

tokens <- function(x) {
  z <- unlist(str_split(norm(x), " "))
  z <- unique(z[nchar(z) >= 3])
  setdiff(z, stop_tokens)
}

semantic_overlap <- function(description, label) {
  a <- tokens(description)
  b <- tokens(label)
  if (length(a) == 0 || length(b) == 0) return(0)
  length(intersect(a, b)) / length(a)
}

# Terms that commonly signal that a target is an analysis-derived endpoint.
derived_pattern <- regex(
  paste(
    c("response","remission","normalization","healing","improvement",
      "responder","estimand","change from baseline","delta",
      "high activity subscore","low activity subscore"),
    collapse="|"
  ),
  ignore_case=TRUE
)

# Structural columns that are safe when exact-name matched.
safe_direct_columns <- c(
  "STUDYID","USUBJID","SUBJID","SITEID","AGE","SEX","RACE","ETHNIC",
  "COUNTRY","ARM","ARMCD","ACTARM","ACTARMCD"
)

# ============================================================
# 4. CLASSIFY THE BEST AUTOMATIC CANDIDATE
# ============================================================

decisions <- overview %>%
  transmute(
    PARAMCD,
    DESCRIPTION,
    AUTO_TRIAGE,
    METADATA_TYPE = AUTO_METADATA_TYPE,
    DATASET = toupper(AUTO_DATASET),
    CODE_VAR = AUTO_CODE_VAR,
    CODE = as.character(AUTO_CODE),
    LABEL_VAR = AUTO_LABEL_VAR,
    LABEL = as.character(AUTO_LABEL),
    SCORE = AUTO_SCORE,
    EXACT = coalesce(AUTO_EXACT_CODE_MATCH, FALSE)
  ) %>%
  rowwise() %>%
  mutate(
    SEMANTIC_OVERLAP = semantic_overlap(DESCRIPTION, LABEL),
    DERIVED_LIKE = str_detect(DESCRIPTION, derived_pattern),
    DECISION = case_when(
      PARAMCD %in% c("VISIT","VISITNUM") ~ "ARD_KEY",
      PARAMCD == "subject_id" ~ "ALIAS_OF_USUBJID",

      EXACT & METADATA_TYPE == "COLUMN" &
        PARAMCD %in% safe_direct_columns ~ "DIRECT_COLUMN",

      EXACT & METADATA_TYPE == "TEST" &
        !DERIVED_LIKE ~ "OBSERVED_CONFIRMED",

      # V2: a strong semantic TEST candidate can be accepted only when:
      #   - scanner classified it STRONG,
      #   - overlap of meaningful target terms with SDTM label is high,
      #   - target does not look like an analysis-derived endpoint.
      AUTO_TRIAGE == "STRONG_TEXT_CANDIDATE" &
        METADATA_TYPE == "TEST" &
        SCORE >= 0.75 &
        SEMANTIC_OVERLAP >= 0.60 &
        !DERIVED_LIKE ~ "OBSERVED_CONFIRMED",

      AUTO_TRIAGE == "NO_AUTOMATIC_CANDIDATE" |
        is.na(DATASET) ~ "NOT_IDENTIFIED",

      DERIVED_LIKE ~ "DERIVABLE_OR_REVIEW",

      TRUE ~ "REVIEW_REQUIRED"
    ),
    DECISION_REASON = case_when(
      DECISION == "ARD_KEY" ~ "Structural visit key.",
      DECISION == "ALIAS_OF_USUBJID" ~ "Alias of USUBJID.",
      DECISION == "DIRECT_COLUMN" ~ "Exact safe SDTM structural/demographic column.",
      DECISION == "OBSERVED_CONFIRMED" & EXACT ~
        "Exact TESTCD/code match; target is not classified as derived-like.",
      DECISION == "OBSERVED_CONFIRMED" & !EXACT ~
        "Strong TEST candidate with high semantic overlap; accepted by V2 generic semantic rule.",
      DECISION == "DERIVABLE_OR_REVIEW" ~
        "Target wording suggests an analysis-derived endpoint; component/candidate requires review.",
      DECISION == "NOT_IDENTIFIED" ~ "No automatic candidate identified.",
      TRUE ~ "Candidate retained for manual clinical/programming review."
    )
  ) %>%
  ungroup()

# ============================================================
# 5. OPTIONAL STUDY-SPECIFIC REVIEWED OVERRIDES
# ============================================================
# Populate ONLY after reviewing scanner output.
#
# Example:
# reviewed_overrides <- tribble(
#   ~PARAMCD, ~METADATA_TYPE, ~DATASET, ~CODE, ~LABEL, ~DECISION, ~DECISION_REASON,
#   "CDAI", "TEST", "QSAI", "CDAI0120", "CDAI01-Total CDAI Score",
#   "OBSERVED_CONFIRMED", "Reviewed: direct total CDAI assessment in this study."
# )
#
reviewed_overrides <- tibble(
  PARAMCD=character(),
  METADATA_TYPE=character(),
  DATASET=character(),
  CODE=character(),
  LABEL=character(),
  DECISION=character(),
  DECISION_REASON=character()
)

if (nrow(reviewed_overrides) > 0) {
  for (i in seq_len(nrow(reviewed_overrides))) {
    p <- reviewed_overrides$PARAMCD[i]
    decisions <- decisions %>% mutate(
      METADATA_TYPE = if_else(PARAMCD == p, reviewed_overrides$METADATA_TYPE[i], METADATA_TYPE),
      DATASET = if_else(PARAMCD == p, toupper(reviewed_overrides$DATASET[i]), DATASET),
      CODE = if_else(PARAMCD == p, reviewed_overrides$CODE[i], CODE),
      LABEL = if_else(PARAMCD == p, reviewed_overrides$LABEL[i], LABEL),
      DECISION = if_else(PARAMCD == p, reviewed_overrides$DECISION[i], DECISION),
      DECISION_REASON = if_else(PARAMCD == p, reviewed_overrides$DECISION_REASON[i], DECISION_REASON)
    )
  }
}

write_csv(decisions, file.path(output_dir, "08_mapping_decisions.csv"), na="")

# ============================================================
# 6. READ SDTM XPT FILES
# ============================================================

xpt_files <- list.files(sdtm_dir, pattern="\\.xpt$", full.names=TRUE, ignore.case=TRUE)
if (length(xpt_files) == 0) stop("No XPT files found.")

xpt_lookup <- setNames(
  xpt_files,
  toupper(tools::file_path_sans_ext(basename(xpt_files)))
)

safe_read <- function(path) {
  tryCatch(read_xpt(path), error=function(e) {
    warning("Could not read ", basename(path), ": ", conditionMessage(e))
    NULL
  })
}

needed <- decisions %>%
  filter(DECISION %in% c("OBSERVED_CONFIRMED","DIRECT_COLUMN")) %>%
  pull(DATASET) %>%
  na.omit() %>%
  unique()

# SV is now explicitly required for the master visit grid; DM for demographics.
needed <- unique(c(needed, "SV", "DM"))
available <- intersect(needed, names(xpt_lookup))

sdtm <- map(available, ~safe_read(xpt_lookup[[.x]]))
names(sdtm) <- available
sdtm <- compact(sdtm)

# ============================================================
# 7. MASTER VISIT GRID - V2
# ============================================================

if ("SV" %in% names(sdtm)) {
  sv <- sdtm[["SV"]]
  if (!"USUBJID" %in% names(sv)) stop("SV exists but has no USUBJID.")

  visit_grid <- sv %>%
    transmute(
      USUBJID = as.character(USUBJID),
      AVISIT = if ("VISIT" %in% names(sv)) as.character(VISIT) else NA_character_,
      AVISITN = if ("VISITNUM" %in% names(sv))
        suppressWarnings(as.numeric(VISITNUM)) else NA_real_
    ) %>%
    filter(!is.na(USUBJID), USUBJID != "") %>%
    distinct()

  visit_grid_source <- "SV"

} else {
  warning("SV not available. Visit grid will be constructed from accepted observed TEST records.")
  visit_grid <- tibble(USUBJID=character(), AVISIT=character(), AVISITN=numeric())
  visit_grid_source <- "OBSERVED_TEST_FALLBACK"
}

# ============================================================
# 8. RESULT EXTRACTION HELPERS
# ============================================================

first_existing <- function(nms, opts) {
  z <- opts[opts %in% nms]
  if (length(z)==0) NA_character_ else z[1]
}

collapse_unique <- function(x, sep=" | ") {
  x <- as.character(x)
  x <- x[!is.na(x) & x != ""]
  if (length(x)==0) return(NA_character_)
  paste(unique(x), collapse=sep)
}

extract_test <- function(paramcd, description, dataset, code, decision_reason, df) {
  nms <- names(df)

  testcd <- first_existing(nms, c(
    paste0(dataset,"TESTCD"), "QSTESTCD","LBTESTCD","MITESTCD","MOTESTCD","FATESTCD"
  ))
  test <- first_existing(nms, c(
    paste0(dataset,"TEST"), "QSTEST","LBTEST","MITEST","MOTEST","FATEST"
  ))

  # Resolve result per row rather than globally: STRESN -> STRESC -> ORRES.
  numv <- first_existing(nms, c(
    paste0(dataset,"STRESN"),"QSSTRESN","LBSTRESN","MISTRESN","MOSTRESN","FASTRESN"
  ))
  charv <- first_existing(nms, c(
    paste0(dataset,"STRESC"),"QSSTRESC","LBSTRESC","MISTRESC","MOSTRESC","FASTRESC"
  ))
  origv <- first_existing(nms, c(
    paste0(dataset,"ORRES"),"QSORRES","LBORRES","MIORRES","MOORRES","FAORRES"
  ))
  unitv <- first_existing(nms, c(
    paste0(dataset,"STRESU"),"QSSTRESU","LBSTRESU","MISTRESU","MOSTRESU","FASTRESU",
    paste0(dataset,"ORRESU"),"QSORRESU","LBORRESU","MIORRESU","MOORRESU","FAORRESU"
  ))
  seqv <- first_existing(nms, c(
    paste0(dataset,"SEQ"),"QSSEQ","LBSEQ","MISEQ","MOSEQ","FASEQ"
  ))
  dtcv <- first_existing(nms, c(
    paste0(dataset,"DTC"),"QSDTC","LBDTC","MIDTC","MODTC","FADTC"
  ))

  if (!"USUBJID" %in% nms || is.na(testcd)) return(tibble())

  z <- df %>% filter(as.character(.data[[testcd]]) == code)
  if (nrow(z)==0) return(tibble())

  val_num  <- if (!is.na(numv))  as.character(z[[numv]])  else rep(NA_character_,nrow(z))
  val_char <- if (!is.na(charv)) as.character(z[[charv]]) else rep(NA_character_,nrow(z))
  val_orig <- if (!is.na(origv)) as.character(z[[origv]]) else rep(NA_character_,nrow(z))

  val_num[val_num==""] <- NA
  val_char[val_char==""] <- NA
  val_orig[val_orig==""] <- NA
  value <- coalesce(val_num, val_char, val_orig)

  tibble(
    USUBJID=as.character(z$USUBJID),
    AVISIT=if ("VISIT" %in% nms) as.character(z$VISIT) else NA_character_,
    AVISITN=if ("VISITNUM" %in% nms) suppressWarnings(as.numeric(z$VISITNUM)) else NA_real_,
    PARAMCD=paramcd,
    DESCRIPTION=description,
    VALUE=value,
    UNIT=if (!is.na(unitv)) as.character(z[[unitv]]) else NA_character_,
    SOURCE_DATASET=dataset,
    SOURCE_CODE_VAR=testcd,
    SOURCE_CODE=as.character(z[[testcd]]),
    SOURCE_TEST=if (!is.na(test)) as.character(z[[test]]) else NA_character_,
    SOURCE_VALUE_VAR=paste(na.omit(c(numv,charv,origv)), collapse=" > "),
    SOURCE_SEQ=if (!is.na(seqv)) as.character(z[[seqv]]) else NA_character_,
    SOURCE_DTC=if (!is.na(dtcv)) as.character(z[[dtcv]]) else NA_character_,
    MAPPING_REASON=decision_reason
  ) %>%
    filter(!is.na(VALUE), VALUE != "")
}

# ============================================================
# 9. EXTRACT ACCEPTED OBSERVED TEST MAPPINGS
# ============================================================

test_map <- decisions %>%
  filter(DECISION=="OBSERVED_CONFIRMED", METADATA_TYPE=="TEST",
         !is.na(DATASET), !is.na(CODE))

trace_long <- pmap_dfr(
  test_map %>% select(PARAMCD,DESCRIPTION,DATASET,CODE,DECISION_REASON),
  function(PARAMCD,DESCRIPTION,DATASET,CODE,DECISION_REASON) {
    ds <- toupper(DATASET)
    if (!ds %in% names(sdtm)) return(tibble())
    extract_test(PARAMCD,DESCRIPTION,ds,CODE,DECISION_REASON,sdtm[[ds]])
  }
)

# SV fallback only if needed.
if (nrow(visit_grid)==0 && nrow(trace_long)>0) {
  visit_grid <- trace_long %>% distinct(USUBJID,AVISIT,AVISITN)
}

# ============================================================
# 10. SUBJECT-LEVEL DIRECT COLUMNS FROM DM
# ============================================================

direct_params <- decisions %>%
  filter(DECISION=="DIRECT_COLUMN") %>%
  pull(PARAMCD)

subject_cols <- tibble(USUBJID=unique(visit_grid$USUBJID))

if ("DM" %in% names(sdtm)) {
  dm <- sdtm[["DM"]]
  wanted <- intersect(unique(c("USUBJID",direct_params)),names(dm))
  if ("USUBJID" %in% wanted) {
    subject_cols <- dm %>%
      select(all_of(wanted)) %>%
      mutate(across(everything(),as.character)) %>%
      distinct(USUBJID,.keep_all=TRUE)
  }
}

# ============================================================
# 11. TRACEABILITY + DUPLICATE REVIEW
# ============================================================

trace_summary <- if (nrow(trace_long)>0) {
  trace_long %>%
    group_by(PARAMCD,DESCRIPTION,SOURCE_DATASET,SOURCE_CODE_VAR,
             SOURCE_CODE,SOURCE_TEST,SOURCE_VALUE_VAR,MAPPING_REASON) %>%
    summarise(
      N_RECORDS=n(),
      N_SUBJECTS=n_distinct(USUBJID),
      N_VISITS=n_distinct(AVISIT[!is.na(AVISIT)&AVISIT!=""]),
      UNITS=collapse_unique(UNIT),
      VISITS=collapse_unique(AVISIT),
      .groups="drop"
    )
} else tibble()

write_csv(trace_summary,file.path(output_dir,"02_traceability_summary.csv"),na="")
write_csv(trace_long,file.path(output_dir,"03_traceability_long.csv"),na="")

duplicate_review <- if (nrow(trace_long)>0) {
  trace_long %>%
    group_by(USUBJID,AVISIT,AVISITN,PARAMCD) %>%
    summarise(
      N_RECORDS=n(),
      N_UNIQUE_VALUES=n_distinct(VALUE),
      VALUES=collapse_unique(VALUE),
      SOURCE_DATASETS=collapse_unique(SOURCE_DATASET),
      SOURCE_SEQS=collapse_unique(SOURCE_SEQ),
      SOURCE_DTCS=collapse_unique(SOURCE_DTC),
      .groups="drop"
    ) %>%
    filter(N_RECORDS>1 | N_UNIQUE_VALUES>1) %>%
    arrange(PARAMCD,USUBJID,AVISITN,AVISIT)
} else tibble()

write_csv(duplicate_review,file.path(output_dir,"04_duplicate_review.csv"),na="")

# ============================================================
# 12. BUILD ARD ON THE SV MASTER GRID
# ============================================================

ard_values <- if (nrow(trace_long)>0) {
  trace_long %>%
    group_by(USUBJID,AVISIT,AVISITN,PARAMCD) %>%
    summarise(VALUE=collapse_unique(VALUE),.groups="drop") %>%
    pivot_wider(
      id_cols=c(USUBJID,AVISIT,AVISITN),
      names_from=PARAMCD,
      values_from=VALUE
    )
} else visit_grid

ard <- visit_grid %>%
  left_join(ard_values,by=c("USUBJID","AVISIT","AVISITN")) %>%
  left_join(subject_cols,by="USUBJID")

if ("subject_id" %in% voi$PARAMCD) ard$subject_id <- ard$USUBJID
if ("VISIT" %in% voi$PARAMCD) ard$VISIT <- ard$AVISIT
if ("VISITNUM" %in% voi$PARAMCD) ard$VISITNUM <- as.character(ard$AVISITN)

for (p in voi$PARAMCD) {
  if (!p %in% names(ard)) ard[[p]] <- NA_character_
}

ard <- ard %>%
  select(USUBJID,AVISIT,AVISITN,all_of(setdiff(voi$PARAMCD,"USUBJID"))) %>%
  arrange(USUBJID,AVISITN,AVISIT)

write_csv(
  ard,
  file.path(output_dir,paste0("05_",safe_study_id,"_SDTM_based_ARD.csv")),
  na=""
)

# ============================================================
# 13. GAP ANALYSIS
# ============================================================

obs_stats <- if (nrow(trace_long)>0) {
  trace_long %>%
    group_by(PARAMCD) %>%
    summarise(
      N_RECORDS=n(),
      N_SUBJECTS=n_distinct(USUBJID),
      N_VISITS=n_distinct(AVISIT[!is.na(AVISIT)&AVISIT!=""]),
      OBSERVED_UNITS=collapse_unique(UNIT),
      OBSERVED_VISITS=collapse_unique(AVISIT),
      .groups="drop"
    )
} else tibble(
  PARAMCD=character(),N_RECORDS=integer(),N_SUBJECTS=integer(),
  N_VISITS=integer(),OBSERVED_UNITS=character(),OBSERVED_VISITS=character()
)

column_stats <- map_dfr(direct_params,function(p) {
  if (!p %in% names(ard)) return(tibble())
  x <- as.character(ard[[p]])
  ok <- !is.na(x)&x!=""
  tibble(
    PARAMCD=p,
    COLUMN_NONMISSING_ROWS=sum(ok),
    COLUMN_SUBJECTS=n_distinct(ard$USUBJID[ok])
  )
})

gap <- decisions %>%
  left_join(obs_stats,by="PARAMCD") %>%
  left_join(column_stats,by="PARAMCD") %>%
  mutate(
    N_RECORDS=coalesce(N_RECORDS,COLUMN_NONMISSING_ROWS,0L),
    N_SUBJECTS=coalesce(N_SUBJECTS,COLUMN_SUBJECTS,0L),
    N_VISITS=coalesce(N_VISITS,0L),
    FINAL_STATUS=case_when(
      DECISION=="OBSERVED_CONFIRMED"&N_RECORDS>0 ~ "FOUND_OBSERVED",
      DECISION=="OBSERVED_CONFIRMED"&N_RECORDS==0 ~ "MAPPED_BUT_NO_VALUES",
      DECISION=="DIRECT_COLUMN"&N_RECORDS>0 ~ "FOUND_DIRECT_COLUMN",
      DECISION=="DIRECT_COLUMN"&N_RECORDS==0 ~ "DIRECT_COLUMN_NO_VALUES",
      DECISION=="ARD_KEY" ~ "ARD_KEY",
      DECISION=="ALIAS_OF_USUBJID" ~ "ALIAS_OF_USUBJID",
      DECISION=="DERIVABLE_OR_REVIEW" ~ "DERIVABLE_OR_REVIEW",
      DECISION=="NOT_IDENTIFIED" ~ "NOT_IDENTIFIED",
      TRUE ~ "REVIEW_REQUIRED"
    )
  ) %>%
  select(
    PARAMCD,DESCRIPTION,FINAL_STATUS,AUTO_TRIAGE,METADATA_TYPE,
    DATASET,CODE,LABEL,SCORE,SEMANTIC_OVERLAP,DERIVED_LIKE,
    N_SUBJECTS,N_RECORDS,N_VISITS,OBSERVED_UNITS,OBSERVED_VISITS,
    DECISION_REASON
  )

write_csv(gap,file.path(output_dir,"01_gap_analysis.csv"),na="")

mapping_used <- gap %>%
  mutate(
    INCLUDED_IN_ARD=FINAL_STATUS %in%
      c("FOUND_OBSERVED","FOUND_DIRECT_COLUMN","ARD_KEY","ALIAS_OF_USUBJID")
  )
write_csv(mapping_used,file.path(output_dir,"06_mapping_used_for_ARD.csv"),na="")

review_queue <- gap %>%
  filter(FINAL_STATUS %in%
    c("REVIEW_REQUIRED","DERIVABLE_OR_REVIEW","MAPPED_BUT_NO_VALUES",
      "DIRECT_COLUMN_NO_VALUES")) %>%
  arrange(desc(SCORE),desc(SEMANTIC_OVERLAP),PARAMCD)
write_csv(review_queue,file.path(output_dir,"07_mapping_review_queue.csv"),na="")

# ============================================================
# 14. VISIT GRID QC
# ============================================================

visit_qc <- visit_grid %>%
  summarise(
    STUDY=study_id,
    GRID_SOURCE=visit_grid_source,
    N_ROWS=n(),
    N_SUBJECTS=n_distinct(USUBJID),
    N_VISITS=n_distinct(AVISIT[!is.na(AVISIT)&AVISIT!=""]),
    VISITS=collapse_unique(AVISIT)
  )

write_csv(visit_qc,file.path(output_dir,"09_visit_grid_qc.csv"),na="")

# ============================================================
# 15. CONSOLE SUMMARY
# ============================================================

cat("\n============================================================\n")
cat("CD SDTM -> GAP + TRACEABILITY + ARD V2\n")
cat("============================================================\n")
cat("Study: ",study_id,"\n",sep="")
cat("Visit grid source: ",visit_grid_source,"\n\n",sep="")

print(gap %>% count(FINAL_STATUS,name="N_VARIABLES") %>% arrange(desc(N_VARIABLES)))

cat("\nARD dimensions:\n")
cat("Rows: ",nrow(ard),"\n",sep="")
cat("Columns: ",ncol(ard),"\n",sep="")
cat("Subjects: ",n_distinct(ard$USUBJID),"\n",sep="")

cat("\nAccepted observed TEST variables: ",nrow(test_map),"\n",sep="")
cat("Traceability records: ",nrow(trace_long),"\n",sep="")
cat("Duplicate/multiple-value keys: ",nrow(duplicate_review),"\n",sep="")

cat("\nOutputs:\n")
cat(normalizePath(output_dir),"\n")
cat("  01_gap_analysis.csv\n")
cat("  02_traceability_summary.csv\n")
cat("  03_traceability_long.csv\n")
cat("  04_duplicate_review.csv\n")
cat("  05_",safe_study_id,"_SDTM_based_ARD.csv\n",sep="")
cat("  06_mapping_used_for_ARD.csv\n")
cat("  07_mapping_review_queue.csv\n")
cat("  08_mapping_decisions.csv\n")
cat("  09_visit_grid_qc.csv\n")
