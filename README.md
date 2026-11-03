# example1

> #!/usr/bin/env Rscript
> # VEGA load-2388: recursive SDTM inventory, 37-variable discovery, reviewed mapping,
> # subject/visit ARD, exploratory candidate ARD, traceability and QC.
> # Source datasets are read-only. Outputs go to a separate folder.
> suppressPackageStartupMessages({
+   library(dplyr); library(tidyr); library(readr); library(stringr)
+   library(purrr); library(tibble)
+ })
> 
> # ---- EDIT ONLY THESE SETTINGS FOR YOUR DOMINO ENVIRONMENT ----
> study_id <- 'CNTO1959UCO2002_VEGA_LOAD2388'
> sdtm_root <- '/domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388'
> output_dir <- file.path(getwd(), 'vega_load2388_full_ard_output')
> # Optional manually approved mappings; the first run creates a template.
> reviewed_mapping_file <- file.path(output_dir, '05_reviewed_mapping_template.csv')
> # ---------------------------------------------------------------
> dir.create(output_dir, showWarnings=FALSE, recursive=TRUE)
> if (!dir.exists(sdtm_root)) stop('SDTM root does not exist: ', sdtm_root)
> 
> voi <- tribble(
+   ~PARAMCD,~DESCRIPTION,~SEARCH_TERMS,~DERIVED,
+   'MAYO','Mayo Score','MAYO|TOTAL MAYO',TRUE,
+   'ENSCORE','Endoscopy Final Score','ENDOSC|MAYO ENDOSC|ENMAYO',TRUE,
+   'RBSCORE','Rectal Bleeding Score','RECTAL BLEED|RBSCORE',FALSE,
+   'SFSCORE','Stool Frequency Score','STOOL FREQUENCY|SFSCORE',FALSE,
+   'ENCSCORE','Endoscopy Central Score (Primary Reader)','CENTRAL|PRIMARY READER|MAYO ENDOSC|ENMAYO',TRUE,
+   'ENLSCORE','Endoscopy Local Score','LOCAL READER|ENMAYO|ENDOSC',TRUE,
+   'UCEISP','Total UCEIS Score (Primary ICE Approach)','UCEIS|UCEISSC',TRUE,
+   'BLEEDP','Bleeding (Primary ICE Approach)','BLEEDING|UCEIS',TRUE,
+   'EROSP','Erosions and Ulcers (Primary ICE Approach)','EROSION|ULCER|UCEIS',TRUE,
+   'VASCP','Vascular Pattern (Primary ICE Approach)','VASCULAR|UCEIS',TRUE,
+   'CRESPP','Clinical Response (Primary Estimand Approach)','CLINICAL RESPONSE|CRESP',TRUE,
+   'HEHL','Histo-Endoscopic Mucosal Healing','HISTO.*ENDOSC|MUCOSAL HEAL',TRUE,
+   'HIHL','Histologic Healing','HISTOLOGIC HEAL|HISTO HEAL',TRUE,
+   'ENHLP','Endoscopic Healing (Primary Estimand Approach)','ENDOSC.*HEAL|ENDOSC.*IMPROV',TRUE,
+   'CREMP','Clinical Remission (Primary Estimand Approach)','CLINICAL REMISSION|CREMP',TRUE,
+   'PMRESPP','Partial Mayo Response (Primary ICE Approach)','PARTIAL MAYO|PMRESP',TRUE,
+   'ARCHCH','Architectural Change (Grade 0)','ARCHITECTURAL|ARCHCH',FALSE,
+   'CHRIINF','Chronic Inflammatory Infiltrate (Grade 1)','CHRONIC INFLAM|CHRIINF',FALSE,
+   'EOS','Eosinophils (10^9/L)','EOSINOPHIL|EOS',FALSE,
+   'NEUTLP','Neutrophils Lamina Propria (Grade 2B)','NEUTROPHIL.*LAMINA|NEUTLP',FALSE,
+   'NEUTEP','Neutrophils Epithelium (Grade 3)','NEUTROPHIL.*EPITHEL|NEUTEP',FALSE,
+   'CRYPTDES','Crypt Destruction (Grade 4)','CRYPT DESTRUCTION|CRYPTDES',FALSE,
+   'ULCER','Erosion or Ulceration (Grade 5)','EROSION|ULCERATION|ULCER',FALSE,
+   'CRPP','C-Reactive Protein (Primary ICE Approach)','C REACTIVE PROTEIN|CRP',TRUE,
+   'CALPPP','Fecal Calprotectin (Primary ICE Approach)','CALPROTECTIN|CALPRO',TRUE,
+   'CORTBL','Induction Baseline Corticosteroid Use','CORTICOSTEROID|STEROID',TRUE,
+   'IBDQTOT','IBDQ Total Score','IBDQ|INFLAMMATORY BOWEL DISEASE QUESTIONNAIRE',FALSE,
+   'PGSCORE','Physician Global Assessment Score','PHYSICIAN GLOBAL|PGSCORE',FALSE,
+   'MOTEST','Modified Mayo Score','MODIFIED MAYO|MMAYO',TRUE,
+   'IBREMP','IBDQ Remission (Primary Estimand Approach)','IBDQ REMISSION|IBREMP',TRUE,
+   'HEHLP','Histo-Endoscopic Mucosal Healing (Primary Estimand Approach)','HISTO.*ENDOSC|MUCOSAL HEAL',TRUE,
+   'ENNRMP','Endoscopic Normalization (Primary Estimand Approach)','ENDOSC.*NORMAL|ENNRM',TRUE,
+   'NANCYHI','Nancy Histological Index','NANCY|NANCYHI',FALSE,
+   'RHI','Robarts Histopathology Index','ROBARTS|RHI',FALSE,
+   'GBTOT','Geboes Total Score','GEBOES|GBTOT',FALSE,
+   'GBHI','Geboes High Activity Subscore','GEBOES|HIGH ACTIVITY|GBHI',TRUE,
+   'GBLO','Geboes Low Activity Subscore','GEBOES|LOW ACTIVITY|GBLO',TRUE
+ )
> stopifnot(nrow(voi)==37, !anyDuplicated(voi$PARAMCD))
> write_csv(voi,file.path(output_dir,'00_variables_of_interest.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_full_ard_output/00_variables_of_interest.csv': No such file or directory
> 
> # Dataset filename convention: mo.sas7bdat.csv / mo.csv / mo.xpt; recursive.
> paths <- list.files(sdtm_root,pattern='\\.(csv|xpt)$',recursive=TRUE,full.names=TRUE,ignore.case=TRUE)
> if (!length(paths)) stop('No .csv/.xpt datasets found recursively under ',sdtm_root)
> base <- basename(paths)
> domain <- toupper(sub('\\.(sas7bdat\\.)?(csv|xpt)$','',base,ignore.case=TRUE))
> fmt <- tolower(tools::file_ext(paths))
> files <- tibble(DATASET=domain,PATH=paths,FORMAT=fmt,BYTES=as.numeric(file.info(paths)$size))
> write_csv(files,file.path(output_dir,'01_file_inventory_all.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_full_ard_output/01_file_inventory_all.csv': No such file or directory
> # Never silently combine same-named domains from different folders/versions.
> dups <- files %>% count(DATASET) %>% filter(n>1)
> if(nrow(dups)) stop('Duplicate dataset names found in multiple folders. Inspect 01_file_inventory_all.csv and set sdtm_root to one version: ',paste(dups$DATASET,collapse=', '))
> 
> read_domain <- function(path,format) {
+   if(format=='xpt') {
+     if(!requireNamespace('haven',quietly=TRUE)) stop('Install haven to read XPT files')
+     z <- as_tibble(haven::read_xpt(path)) %>% mutate(across(everything(),as.character))
+   } else {
+     z <- read_csv(path,col_types=cols(.default=col_character()),show_col_types=FALSE,progress=FALSE,name_repair='minimal')
+   }
+   names(z) <- toupper(trimws(names(z)))
+   if(anyDuplicated(names(z))) stop('Duplicate column names in ',path)
+   z
+ }
> clean <- function(x) { x<-as.character(x); x[is.na(x)]<-''; trimws(x) }
> getcol <- function(df,nm) if(nm %in% names(df)) clean(df[[nm]]) else rep('',nrow(df))
> result_value <- function(df,prefix) {
+   a<-getcol(df,paste0(prefix,'STRESN'))
+   b<-getcol(df,paste0(prefix,'STRESC'))
+   c<-getcol(df,paste0(prefix,'ORRES'))
+   ifelse(nzchar(a),a,ifelse(nzchar(b),b,c))
+ }
> 
> metadata_list<-list(); observed_list<-list(); coverage_list<-list(); sv_grid<-NULL; dm_subjects<-NULL
> for(i in seq_len(nrow(files))) {
+   f<-files[i,]; nm<-f$DATASET
+   cat('Reading ',nm,': ',f$PATH,'\n',sep='')
+   z<-tryCatch(read_domain(f$PATH,f$FORMAT),error=function(e) stop('Cannot read ',f$PATH,': ',conditionMessage(e)))
+   coverage_list[[nm]]<-tibble(DATASET=nm,N_ROWS=nrow(z),N_COLS=ncol(z),N_SUBJECTS=if('USUBJID'%in%names(z))n_distinct(z$USUBJID[nzchar(clean(z$USUBJID))]) else NA_integer_,COLUMN_NAMES=paste(names(z),collapse=' | '))
+   if(nm=='SV' && 'USUBJID'%in%names(z)) sv_grid<-tibble(USUBJID=getcol(z,'USUBJID'),AVISIT=getcol(z,'VISIT'),AVISITN=suppressWarnings(as.numeric(getcol(z,'VISITNUM')))) %>% filter(nzchar(USUBJID)) %>% distinct()
+   if(nm=='DM' && 'USUBJID'%in%names(z)) dm_subjects<-tibble(USUBJID=getcol(z,'USUBJID')) %>% filter(nzchar(USUBJID)) %>% distinct()
+   if(!'USUBJID'%in%names(z)) next
+   # Findings datasets with paired TESTCD/TEST, plus supplemental QNAM/QLABEL.
+   code_cols<-grep('TESTCD$',names(z),value=TRUE)
+   if(all(c('QNAM','QVAL')%in%names(z))) code_cols<-c(code_cols,'QNAM')
+   for(cc in code_cols) {
+     prefix<-if(cc=='QNAM') 'SUPP' else sub('TESTCD$','',cc)
+     labcol<-if(cc=='QNAM') 'QLABEL' else paste0(prefix,'TEST')
+     codes<-getcol(z,cc); labels<-getcol(z,labcol)
+     ok<-nzchar(codes)
+     if(!any(ok)) next
+     meta<-tibble(DATASET=nm,CODE_VAR=cc,CODE=codes[ok],LABEL=labels[ok]) %>% count(DATASET,CODE_VAR,CODE,LABEL,name='N_RECORDS')
+     metadata_list[[length(metadata_list)+1]]<-meta
+     values<-if(cc=='QNAM')getcol(z,'QVAL') else result_value(z,prefix)
+     observed_list[[length(observed_list)+1]]<-tibble(
+       USUBJID=getcol(z,'USUBJID')[ok],AVISIT=getcol(z,'VISIT')[ok],AVISITN=suppressWarnings(as.numeric(getcol(z,'VISITNUM')[ok])),
+       DATASET=nm,CODE_VAR=cc,CODE=codes[ok],LABEL=labels[ok],VALUE=values[ok],
+       UNIT=if(cc=='QNAM')rep('',sum(ok)) else getcol(z,paste0(prefix,'STRESU'))[ok],
+       SOURCE_SEQ=if(cc=='QNAM')getcol(z,'IDVARVAL')[ok] else getcol(z,paste0(prefix,'SEQ'))[ok],
+       SOURCE_DTC=if(cc=='QNAM')rep('',sum(ok)) else getcol(z,paste0(prefix,'DTC'))[ok],
+       EVALUATOR=if(cc=='QNAM')rep('',sum(ok)) else getcol(z,paste0(prefix,'EVAL'))[ok],
+       EVALUATOR_ID=if(cc=='QNAM')rep('',sum(ok)) else getcol(z,paste0(prefix,'EVALID'))[ok],
+       CATEGORY=if(cc=='QNAM')rep('',sum(ok)) else getcol(z,paste0(prefix,'CAT'))[ok],
+       SUBCATEGORY=if(cc=='QNAM')rep('',sum(ok)) else getcol(z,paste0(prefix,'SCAT'))[ok],
+       SUPP_IDVAR=if(cc=='QNAM')getcol(z,'IDVAR')[ok] else rep('',sum(ok)),
+       SOURCE_FILE=basename(f$PATH)
+     )
+   }
+   rm(z); gc(verbose=FALSE)
+ }
Reading AE.SAS7BDAT.CSV.CLEAN: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ae.sas7bdat.csv.clean.csv
Error in value[[3L]](cond) : 
  Cannot read /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ae.sas7bdat.csv.clean.csv: unused arguments (show_col_types = FALSE, name_repair = "minimal")
> coverage<-bind_rows(coverage_list)
> write_csv(coverage,file.path(output_dir,'02_dataset_coverage.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_full_ard_output/02_dataset_coverage.csv': No such file or directory
> metadata<-bind_rows(metadata_list) %>% distinct()
> if(!nrow(metadata))stop('No TESTCD or QNAM metadata found')
Error: No TESTCD or QNAM metadata found
> write_csv(metadata,file.path(output_dir,'03_all_test_metadata.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_full_ard_output/03_all_test_metadata.csv': No such file or directory
> obs<-bind_rows(observed_list)
> # Source data are preserved separately; no cross-domain or cross-load record merging.
> write_csv(obs,file.path(output_dir,'04_all_findings_long.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_full_ard_output/04_all_findings_long.csv': No such file or directory
> 
> # Candidate matches are intentionally broad; NOT clinical validation.
> candidates<-map_dfr(seq_len(nrow(voi)),function(i){
+   v<-voi[i,]
+   z<-metadata %>% filter(str_detect(str_to_upper(paste(CODE,LABEL)),regex(v$SEARCH_TERMS,ignore_case=TRUE)))
+   if(!nrow(z))return(tibble())
+   z %>% mutate(PARAMCD=v$PARAMCD,DESCRIPTION=v$DESCRIPTION,DERIVED=v$DERIVED,
+     EXACT_CODE=toupper(CODE)==v$PARAMCD) %>%
+     select(PARAMCD,DESCRIPTION,DERIVED,DATASET,CODE_VAR,CODE,LABEL,N_RECORDS,EXACT_CODE)
+ })
 Error: Problem with `filter()` input `..1`.
ℹ Input `..1` is `str_detect(...)`.
x object 'CODE' not found
Run `rlang::last_error()` to see where the error occurred. > write_csv(candidates,file.path(output_dir,'06_mapping_candidates.csv'),na='')
Error in is.data.frame(x) : object 'candidates' not found
> 
> # Safe default: exact TESTCD for NON-DERIVED variables only. Even these require
> # review of units/reader/timepoint before treating the ARD as clinically validated.
> # Avoid ULCER (histology) vs EROSP (UCEIS), EOS lab vs adverse event text, etc.
> unsafe_auto<-c('ENSCORE','ENCSCORE','ENLSCORE','BLEEDP','EROSP','VASCP','ULCER','EOS','RHI','PGSCORE')
> auto <- candidates %>% filter(EXACT_CODE,!DERIVED,!PARAMCD %in% unsafe_auto,CODE_VAR!='QNAM') %>%
+   group_by(PARAMCD) %>% filter(n()==1) %>% ungroup() %>%
+   transmute(PARAMCD,DATASET,CODE_VAR,CODE,EVALUATOR_FILTER='',CATEGORY_FILTER='',APPROVED='YES',REVIEW_NOTE='AUTO_EXACT_CODE_PROVISIONAL; validate before clinical use')
Error in filter(., EXACT_CODE, !DERIVED, !PARAMCD %in% unsafe_auto, CODE_VAR !=  : 
  object 'candidates' not found
> # Write template only on first run, never overwrite user's reviewed edits.
> if(!file.exists(reviewed_mapping_file)) {
+   template<-candidates %>% arrange(PARAMCD,desc(EXACT_CODE),desc(N_RECORDS)) %>%
+     transmute(PARAMCD,DATASET,CODE_VAR,CODE,EVALUATOR_FILTER='',CATEGORY_FILTER='',APPROVED='NO',REVIEW_NOTE=paste0('CANDIDATE ONLY: ',LABEL))
+   write_csv(template,reviewed_mapping_file,na='')
+ }
 Error in arrange(., PARAMCD, desc(EXACT_CODE), desc(N_RECORDS)) : 
  object 'candidates' not found > manual<-read_csv(reviewed_mapping_file,col_types=cols(.default=col_character()),show_col_types=FALSE) %>%
+   filter(toupper(trimws(APPROVED))=='YES') %>%
+   select(PARAMCD,DATASET,CODE_VAR,CODE,EVALUATOR_FILTER,CATEGORY_FILTER,APPROVED,REVIEW_NOTE)
Error in read_csv(reviewed_mapping_file, col_types = cols(.default = col_character()),  : 
  unused argument (show_col_types = FALSE)
> # Manual approved mapping replaces provisional automatic mapping for the same target.
> accepted<-bind_rows(auto %>% filter(!PARAMCD %in% manual$PARAMCD),manual) %>%
+   mutate(across(c(PARAMCD,DATASET,CODE_VAR,CODE),toupper))
Error in filter(., !PARAMCD %in% manual$PARAMCD) : 
  object 'auto' not found
> # One approved rule per target, to avoid silently combining readers/codes.
> if(anyDuplicated(accepted$PARAMCD))stop('Multiple approved mappings for a PARAMCD; resolve in template first')
Error in anyDuplicated(accepted$PARAMCD) : object 'accepted' not found
> write_csv(accepted,file.path(output_dir,'07_mapping_rules_used.csv'),na='')
Error in is.data.frame(x) : object 'accepted' not found
> 
> # Candidate traceability, including evaluator and visit. A candidate is not a confirmed endpoint.
> key_candidates<-candidates %>% distinct(PARAMCD,DATASET,CODE_VAR,CODE)
Error in distinct(., PARAMCD, DATASET, CODE_VAR, CODE) : 
  object 'candidates' not found
> all_candidate_records<-obs %>% inner_join(key_candidates,by=c('DATASET','CODE_VAR','CODE')) %>%
+   filter(nzchar(VALUE))
Error in is.data.frame(y) : object 'key_candidates' not found
> write_csv(all_candidate_records,file.path(output_dir,'08_candidate_traceability_long.csv'),na='')
Error in is.data.frame(x) : object 'all_candidate_records' not found
> candidate_qc<-all_candidate_records %>% group_by(PARAMCD,DATASET,CODE,EVALUATOR,EVALUATOR_ID,AVISIT,AVISITN) %>%
+   summarise(N_RECORDS=n(),N_SUBJECTS=n_distinct(USUBJID),N_VALUES=n_distinct(VALUE),.groups='drop')
Error in group_by(., PARAMCD, DATASET, CODE, EVALUATOR, EVALUATOR_ID,  : 
  object 'all_candidate_records' not found
> write_csv(candidate_qc,file.path(output_dir,'09_candidate_coverage_by_visit_reader.csv'),na='')
Error in is.data.frame(x) : object 'candidate_qc' not found
> 
> approved_records<-map_dfr(seq_len(nrow(accepted)),function(i){
+   r<-accepted[i,]
+   x<-obs %>% filter(DATASET==r$DATASET,CODE_VAR==r$CODE_VAR,CODE==r$CODE,nzchar(VALUE))
+   if(nzchar(clean(r$EVALUATOR_FILTER))) x<-x %>% filter(toupper(EVALUATOR)==toupper(r$EVALUATOR_FILTER))
+   if(nzchar(clean(r$CATEGORY_FILTER))) x<-x %>% filter(toupper(CATEGORY)==toupper(r$CATEGORY_FILTER))
+   x %>% mutate(PARAMCD=r$PARAMCD,REVIEW_NOTE=r$REVIEW_NOTE)
+ })
Error in nrow(accepted) : object 'accepted' not found
> if(!nrow(accepted)) approved_records <- obs[0,] %>% mutate(PARAMCD=character(),REVIEW_NOTE=character())
Error in nrow(accepted) : object 'accepted' not found
> write_csv(approved_records,file.path(output_dir,'10_approved_traceability_long.csv'),na='')
Error in is.data.frame(x) : object 'approved_records' not found
> 
> # IMPORTANT: SUPP-- has no direct visit. Do not map it to subject/visit without
> # linking RDOMAIN/IDVAR/IDVARVAL to the parent --SEQ and then visit.
> if(nrow(approved_records) && any(approved_records$CODE_VAR=='QNAM')) stop('SUPP mapping approved but parent record join is not implemented. Remove SUPP approval; use SUPP for discovery only.')
Error in nrow(approved_records) : object 'approved_records' not found
> 
> if(is.null(sv_grid)||!nrow(sv_grid)) {
+   warning('SV unavailable: building visit grid from findings. Coverage may be incomplete.')
+   grid<-obs %>% filter(nzchar(USUBJID),nzchar(AVISIT)|!is.na(AVISITN)) %>% distinct(USUBJID,AVISIT,AVISITN)
+   grid_source<-'FINDINGS_FALLBACK'
+ } else {grid<-sv_grid;grid_source<-'SV'}
Error: Problem with `filter()` input `..1`.
ℹ Input `..1` is `nzchar(USUBJID)`.
x object 'USUBJID' not found
Run `rlang::last_error()` to see where the error occurred.
In addition: Warning message:
 Error: Problem with `filter()` input `..1`.
ℹ Input `..1` is `nzchar(USUBJID)`.
x object 'USUBJID' not found
Run `rlang::last_error()` to see where the error occurred. > # Add observed visits not present in SV, but report them separately.
> observed_grid<-obs %>% filter(nzchar(USUBJID),nzchar(AVISIT)|!is.na(AVISITN)) %>% distinct(USUBJID,AVISIT,AVISITN)
Error: Problem with `filter()` input `..1`.
ℹ Input `..1` is `nzchar(USUBJID)`.
x object 'USUBJID' not found
Run `rlang::last_error()` to see where the error occurred.
> missing_from_sv<-if(grid_source=='SV')anti_join(observed_grid,grid,by=c('USUBJID','AVISIT','AVISITN')) else tibble()
Error: object 'grid_source' not found
> write_csv(missing_from_sv,file.path(output_dir,'11_visits_not_in_sv.csv'),na='')
Error in is.data.frame(x) : object 'missing_from_sv' not found
> # Union ensures observed results are not lost because of mismatched visit labels.
> grid<-bind_rows(grid,observed_grid) %>% distinct() %>% arrange(USUBJID,AVISITN,AVISIT)
Error in list2(...) : object 'observed_grid' not found
> 
> # AVAL/AVALC based on all values for the target, not individual cells.
> if(nrow(approved_records)) {
+   dict<-approved_records %>% group_by(PARAMCD) %>% summarise(
+     DATA_SOURCE=paste(sort(unique(DATASET)),collapse='_'),
+     RESULT_TYPE=if(all(!is.na(suppressWarnings(as.numeric(VALUE))))) 'AVAL' else 'AVALC',.groups='drop') %>%
+     mutate(ARD_COLUMN=paste0(DATA_SOURCE,'_PARAMCD_',PARAMCD,'_',RESULT_TYPE))
+   tmp<-approved_records %>% left_join(dict %>% select(PARAMCD,ARD_COLUMN),by='PARAMCD')
+   # Conflicts are NOT silently resolved using last/first/smallest.
+   conflicts<-tmp %>% group_by(USUBJID,AVISIT,AVISITN,PARAMCD,ARD_COLUMN) %>% summarise(
+     N_RECORDS=n(),N_UNIQUE_VALUES=n_distinct(VALUE),VALUES=paste(unique(VALUE),collapse=' | '),
+     SOURCE_SEQS=paste(unique(SOURCE_SEQ),collapse=' | '),EVALUATORS=paste(unique(EVALUATOR),collapse=' | '),.groups='drop') %>%
+     filter(N_RECORDS>1 | N_UNIQUE_VALUES>1)
+   write_csv(conflicts,file.path(output_dir,'12_duplicate_conflict_qc.csv'),na='')
+   # Keep conflicting cells blank; values remain available in traceability/QC.
+   wide<-tmp %>% group_by(USUBJID,AVISIT,AVISITN,ARD_COLUMN) %>% summarise(
+     VALUE=if(n_distinct(VALUE)==1) first(VALUE) else NA_character_,.groups='drop') %>%
+     pivot_wider(names_from=ARD_COLUMN,values_from=VALUE)
+   ard<-grid %>% left_join(wide,by=c('USUBJID','AVISIT','AVISITN'))
+ } else {
+   dict<-tibble(PARAMCD=character(),DATA_SOURCE=character(),RESULT_TYPE=character(),ARD_COLUMN=character())
+   conflicts<-tibble(); ard<-grid
+   write_csv(conflicts,file.path(output_dir,'12_duplicate_conflict_qc.csv'),na='')
+ }
Error in nrow(approved_records) : object 'approved_records' not found
> write_csv(dict,file.path(output_dir,'13_ard_column_dictionary.csv'),na='')
Error in is.data.frame(x) : object 'dict' not found
> write_csv(ard,file.path(output_dir,'14_VEGA_load2388_SDTM_ARD_PROVISIONAL.csv'),na='')
Error in is.data.frame(x) : object 'ard' not found
> 
> # All candidates can also be inspected in a separate wide ARD with explicit CANDIDATE prefix.
> # Distinct source code + reader are kept separate; no clinical equivalence implied.
> if(nrow(all_candidate_records)) {
+   cand_wide<-all_candidate_records %>% mutate(
+     SOURCE_KEY=paste0('CANDIDATE_',make.names(DATASET),'_',make.names(CODE),'_',make.names(EVALUATOR),'_FOR_',PARAMCD)) %>%
+     group_by(USUBJID,AVISIT,AVISITN,SOURCE_KEY) %>%
+     summarise(VALUE=if(n_distinct(VALUE)==1) first(VALUE) else NA_character_,.groups='drop') %>%
+     pivot_wider(names_from=SOURCE_KEY,values_from=VALUE)
+   write_csv(grid %>% left_join(cand_wide,by=c('USUBJID','AVISIT','AVISITN')),
+     file.path(output_dir,'15_VEGA_load2388_CANDIDATE_ARD_NOT_VALIDATED.csv'),na='')
+ }
Error in nrow(all_candidate_records) : 
  object 'all_candidate_records' not found
> 
> summary<-voi %>% left_join(accepted %>% select(PARAMCD,DATASET,CODE,REVIEW_NOTE),by='PARAMCD') %>%
+   left_join(approved_records %>% group_by(PARAMCD) %>% summarise(N_RECORDS=n(),N_SUBJECTS=n_distinct(USUBJID),.groups='drop'),by='PARAMCD') %>%
+   left_join(candidates %>% count(PARAMCD,name='N_CANDIDATES'),by='PARAMCD') %>%
+   mutate(N_RECORDS=coalesce(N_RECORDS,0L),N_SUBJECTS=coalesce(N_SUBJECTS,0L),N_CANDIDATES=coalesce(N_CANDIDATES,0L),
+     STATUS=case_when(N_RECORDS>0~'EXTRACTED_PROVISIONAL',!is.na(DATASET)~'APPROVED_RULE_NO_RECORDS',N_CANDIDATES>0~'CANDIDATES_REQUIRE_REVIEW',TRUE~'NOT_IDENTIFIED_IN_SCANNER')) %>%
+   select(PARAMCD,DESCRIPTION,DERIVED,STATUS,DATASET,CODE,N_RECORDS,N_SUBJECTS,N_CANDIDATES,REVIEW_NOTE)
Error in select(., PARAMCD, DATASET, CODE, REVIEW_NOTE) : 
  object 'accepted' not found
> write_csv(summary,file.path(output_dir,'16_37_variable_gap_summary.csv'),na='')
Error in write_delim(x, file, delim = ",", na = na, append = append, col_names = col_names,  : 
  is.data.frame(x) is not TRUE
> write_csv(tibble(STUDY=study_id,GRID_SOURCE=grid_source,N_ROWS=nrow(ard),N_SUBJECTS=n_distinct(ard$USUBJID),N_VISITS=n_distinct(ard$AVISIT),N_APPROVED_VARIABLES=nrow(accepted),N_EXTRACTED_VARIABLES=sum(summary$N_RECORDS>0),N_CONFLICT_KEYS=nrow(conflicts)),file.path(output_dir,'17_ard_qc_summary.csv'),na='')
Error in eval_tidy(xs[[j]], mask) : object 'grid_source' not found
> cat('\nFINISHED: ',output_dir,'\n',sep='')

FINISHED: /domino/vega_load2388_full_ard_output
> print(summary %>% count(STATUS))
Error in UseMethod("count") : 
  no applicable method for 'count' applied to an object of class "function"
> cat('ARD: ',nrow(ard),' rows x ',ncol(ard),' columns; ',n_distinct(ard$USUBJID),' subjects\n',sep='')
Error in nrow(ard) : object 'ard' not found
> cat('Review 05_reviewed_mapping_template.csv and rerun after approving mappings.\n')
Review 05_reviewed_mapping_template.csv and rerun after approving mappings.
> cat('CAUTION: provisional SDTM ARD is not equivalent to ADaM estimand-derived ARD.\n')
CAUTION: provisional SDTM ARD is not equivalent to ADaM estimand-derived ARD.
