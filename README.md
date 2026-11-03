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
> # ============================================================
> # VEGA - SDTM load-2388 | Full UC Variable Mapping + ARD
> # ============================================================
> 
> library(dplyr)
> library(tidyr)
> library(readr)
> library(stringr)
> library(purrr)
> library(tibble)
> 
> CONFIG <- list(
+   study_id = "CNTO1959UCO2002_VEGA",
+   
+   input_dir = paste0(
+     "/domino/datasets/local/clinical-trial-data/",
+     "CNTO1959UCO2002-VEGA-WK50/load-2388/Data"
+   ),
+   
+   output_dir = "/domino/vega_load2388_ard",
+   
+   output_dataset = "vega_load2388_sdtm_ard.csv",
+   mapping_report = "vega_load2388_mapping.csv",
+   qc_report = "vega_load2388_qc.csv"
+ )
> 
> # Compatibility with the existing script
> study_id <- CONFIG$study_id
> sdtm_root <- CONFIG$input_dir
> output_dir <- CONFIG$output_dir
> 
> reviewed_mapping_file <- file.path(
+   output_dir,
+   "05_reviewed_mapping_template.csv"
+ )
> 
> dir.create(
+   output_dir,
+   recursive = TRUE,
+   showWarnings = FALSE
+ )
> 
> if (!dir.exists(sdtm_root)) {
+   stop("Input directory not found: ", sdtm_root)
+ }
> 
> if (!dir.exists(output_dir)) {
+   stop("Could not create output directory: ", output_dir)
+ }
Error: Could not create output directory: /domino/vega_load2388_ard
> 
> cat("Study:", study_id, "\n")
Study: CNTO1959UCO2002_VEGA 
> cat("Input:", sdtm_root, "\n")
Input: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data 
> cat("Output:", output_dir, "\n")
Output: /domino/vega_load2388_ard 
> 
> # ---------------------------------------------------------------
> dir.create(output_dir, showWarnings=FALSE, recursive=TRUE)
> if (!dir.exists(output_dir) || file.access(output_dir, 2) != 0) stop('Output directory not writable: ', output_dir, '. Set VEGA_OUTPUT_DIR to a writable path.')
Error: Output directory not writable: /domino/vega_load2388_ard. Set VEGA_OUTPUT_DIR to a writable path.
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
  cannot open file '/domino/vega_load2388_ard/00_variables_of_interest.csv': No such file or directory
> 
> # Dataset filename convention: mo.sas7bdat.csv / mo.csv / mo.xpt; recursive.
> paths <- list.files(sdtm_root,pattern='\\.(csv|xpt)$',recursive=TRUE,full.names=TRUE,ignore.case=TRUE)
> if (!length(paths)) stop('No .csv/.xpt datasets found recursively under ',sdtm_root)
> base <- basename(paths)
> domain <- toupper(sub('\\.(sas7bdat\\.csv\\.clean\\.csv|sas7bdat\\.csv|csv|xpt)$','',base,ignore.case=TRUE))
> fmt <- tolower(tools::file_ext(paths))
> files <- tibble(DATASET=domain,PATH=paths,FORMAT=fmt,BYTES=as.numeric(file.info(paths)$size))
> write_csv(files,file.path(output_dir,'01_file_inventory_all.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/01_file_inventory_all.csv': No such file or directory
> # Never silently combine same-named domains from different folders/versions.
> # If both cleaned and original files exist for a domain, inspect and select one source first.
> dups <- files %>% count(DATASET) %>% filter(n>1)
> if(nrow(dups)) stop('Duplicate dataset names found in multiple folders. Inspect 01_file_inventory_all.csv and set sdtm_root to one version: ',paste(dups$DATASET,collapse=', '))
Error: Duplicate dataset names found in multiple folders. Inspect 01_file_inventory_all.csv and set sdtm_root to one version: AE, CM, CO, DA, DD, DM, DS, DV, EC, EX, FA, HO, IE, IS, LB, MB, MH, MI, MO, PC, PF, PR, QS, RELREC, SE, SR, SU, SUPPAE, SUPPCM, SUPPDA, SUPPDM, SUPPDS, SUPPDV, SUPPEC, SUPPFA, SUPPHO, SUPPIS, SUPPLB, SUPPMH, SUPPMI, SUPPMO, SUPPPC, SUPPPF, SUPPPR, SUPPQS, SUPPSU, SV, TA, TE, TI, TS, TV, VS, XZ, ZR
> 
> read_domain <- function(path,format) {
+   if(format=='xpt') {
+     if(!requireNamespace('haven',quietly=TRUE)) stop('Install haven to read XPT files')
+     z <- as_tibble(haven::read_xpt(path)) %>% mutate(across(everything(),as.character))
+   } else {
+     z <- readr::read_csv(path, col_types=readr::cols(.default=readr::col_character()), progress=FALSE)
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
Reading AE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ae.sas7bdat.csv.clean.csv
Reading CM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/cm.sas7bdat.csv.clean.csv
Reading CO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/co.sas7bdat.csv.clean.csv
Reading DA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/da.sas7bdat.csv.clean.csv
Reading DD: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/dd.sas7bdat.csv.clean.csv
Reading DM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/dm.sas7bdat.csv.clean.csv
Reading DS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ds.sas7bdat.csv.clean.csv
Reading DV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/dv.sas7bdat.csv.clean.csv
Reading EC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ec.sas7bdat.csv.clean.csv
Reading EX: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ex.sas7bdat.csv.clean.csv
Reading FA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/fa.sas7bdat.csv.clean.csv
Reading HO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ho.sas7bdat.csv.clean.csv
Reading IE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ie.sas7bdat.csv.clean.csv
Reading IS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/is.sas7bdat.csv.clean.csv
Reading LB: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/lb.sas7bdat.csv.clean.csv
Reading MB: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/mb.sas7bdat.csv.clean.csv
Reading MH: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/mh.sas7bdat.csv.clean.csv
Reading MI: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/mi.sas7bdat.csv.clean.csv
Reading MO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/mo.sas7bdat.csv.clean.csv
Reading PC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/pc.sas7bdat.csv.clean.csv
Reading PF: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/pf.sas7bdat.csv.clean.csv
Reading PR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/pr.sas7bdat.csv.clean.csv
Reading QS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/qs.sas7bdat.csv.clean.csv
Reading RELREC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/relrec.sas7bdat.csv.clean.csv
Reading SE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/se.sas7bdat.csv.clean.csv
Reading SR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/sr.sas7bdat.csv.clean.csv
Reading SU: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/su.sas7bdat.csv.clean.csv
Reading SUPPAE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppae.sas7bdat.csv.clean.csv
Reading SUPPCM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppcm.sas7bdat.csv.clean.csv
Reading SUPPDA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppda.sas7bdat.csv.clean.csv
Reading SUPPDM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppdm.sas7bdat.csv.clean.csv
Reading SUPPDS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppds.sas7bdat.csv.clean.csv
Reading SUPPDV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppdv.sas7bdat.csv.clean.csv
Reading SUPPEC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppec.sas7bdat.csv.clean.csv
Reading SUPPFA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppfa.sas7bdat.csv.clean.csv
Reading SUPPHO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppho.sas7bdat.csv.clean.csv
Reading SUPPIS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppis.sas7bdat.csv.clean.csv
Reading SUPPLB: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/supplb.sas7bdat.csv.clean.csv
Reading SUPPMH: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppmh.sas7bdat.csv.clean.csv
Reading SUPPMI: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppmi.sas7bdat.csv.clean.csv
Reading SUPPMO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppmo.sas7bdat.csv.clean.csv
Reading SUPPPC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/supppc.sas7bdat.csv.clean.csv
Reading SUPPPF: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/supppf.sas7bdat.csv.clean.csv
Reading SUPPPR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/supppr.sas7bdat.csv.clean.csv
Reading SUPPQS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppqs.sas7bdat.csv.clean.csv
Reading SUPPSU: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/suppsu.sas7bdat.csv.clean.csv
Reading SV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/sv.sas7bdat.csv.clean.csv
Reading TA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ta.sas7bdat.csv.clean.csv
Reading TE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/te.sas7bdat.csv.clean.csv
Reading TI: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ti.sas7bdat.csv.clean.csv
Reading TS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/ts.sas7bdat.csv.clean.csv
Reading TV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/tv.sas7bdat.csv.clean.csv
Reading VS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/vs.sas7bdat.csv.clean.csv
Reading XZ: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/xz.sas7bdat.csv.clean.csv
Reading ZR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/cleaned/zr.sas7bdat.csv.clean.csv
Reading AE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ae.sas7bdat.csv
Reading CM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/cm.sas7bdat.csv
Reading CO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/co.sas7bdat.csv
Reading DA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/da.sas7bdat.csv
Reading DD: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/dd.sas7bdat.csv
Reading DM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/dm.sas7bdat.csv
Reading DS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ds.sas7bdat.csv
Reading DV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/dv.sas7bdat.csv
Reading EC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ec.sas7bdat.csv
Reading EX: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ex.sas7bdat.csv
Reading FA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/fa.sas7bdat.csv
Reading HO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ho.sas7bdat.csv
Reading IE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ie.sas7bdat.csv
Reading IS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/is.sas7bdat.csv
Reading LB: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/lb.sas7bdat.csv
Reading MB: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/mb.sas7bdat.csv
Reading MH: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/mh.sas7bdat.csv
Reading MI: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/mi.sas7bdat.csv
Reading MO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/mo.sas7bdat.csv
Reading PC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/pc.sas7bdat.csv
Reading PF: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/pf.sas7bdat.csv
Reading PR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/pr.sas7bdat.csv
Reading QS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/qs.sas7bdat.csv
Reading RELREC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/relrec.sas7bdat.csv
Reading SE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/se.sas7bdat.csv
Reading SR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/sr.sas7bdat.csv
Reading SU: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/su.sas7bdat.csv
Reading SUPPAE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppae.sas7bdat.csv
Reading SUPPCM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppcm.sas7bdat.csv
Reading SUPPDA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppda.sas7bdat.csv
Reading SUPPDM: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppdm.sas7bdat.csv
Reading SUPPDS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppds.sas7bdat.csv
Reading SUPPDV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppdv.sas7bdat.csv
Reading SUPPEC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppec.sas7bdat.csv
Reading SUPPFA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppfa.sas7bdat.csv
Reading SUPPHO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppho.sas7bdat.csv
Reading SUPPIS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppis.sas7bdat.csv
Reading SUPPLB: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/supplb.sas7bdat.csv
Reading SUPPMH: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppmh.sas7bdat.csv
Reading SUPPMI: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppmi.sas7bdat.csv
Reading SUPPMO: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppmo.sas7bdat.csv
Reading SUPPPC: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/supppc.sas7bdat.csv
Reading SUPPPF: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/supppf.sas7bdat.csv
Reading SUPPPR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/supppr.sas7bdat.csv
Reading SUPPQS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppqs.sas7bdat.csv
Reading SUPPSU: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/suppsu.sas7bdat.csv
Reading SV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/sv.sas7bdat.csv
Reading TA: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ta.sas7bdat.csv
Reading TE: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/te.sas7bdat.csv
Reading TI: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ti.sas7bdat.csv
Reading TS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/ts.sas7bdat.csv
Reading TV: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/tv.sas7bdat.csv
Reading VS: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/vs.sas7bdat.csv
Reading XZ: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/xz.sas7bdat.csv
Reading ZR: /domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv/zr.sas7bdat.csv
> coverage<-bind_rows(coverage_list)
> write_csv(coverage,file.path(output_dir,'02_dataset_coverage.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/02_dataset_coverage.csv': No such file or directory
> metadata<-bind_rows(metadata_list) %>% distinct()
> if(!nrow(metadata))stop('No TESTCD or QNAM metadata found')
> write_csv(metadata,file.path(output_dir,'03_all_test_metadata.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/03_all_test_metadata.csv': No such file or directory
> obs<-bind_rows(observed_list)
> # Source data are preserved separately; no cross-domain or cross-load record merging.
> write_csv(obs,file.path(output_dir,'04_all_findings_long.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/04_all_findings_long.csv': No such file or directory
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
> write_csv(candidates,file.path(output_dir,'06_mapping_candidates.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/06_mapping_candidates.csv': No such file or directory
> 
> # Safe default: exact TESTCD for NON-DERIVED variables only. Even these require
> # review of units/reader/timepoint before treating the ARD as clinically validated.
> # Avoid ULCER (histology) vs EROSP (UCEIS), EOS lab vs adverse event text, etc.
> unsafe_auto<-c('ENSCORE','ENCSCORE','ENLSCORE','BLEEDP','EROSP','VASCP','ULCER','EOS','RHI','PGSCORE')
> auto <- candidates %>% filter(EXACT_CODE,!DERIVED,!PARAMCD %in% unsafe_auto,CODE_VAR!='QNAM') %>%
+   group_by(PARAMCD) %>% filter(n()==1) %>% ungroup() %>%
+   transmute(PARAMCD,DATASET,CODE_VAR,CODE,EVALUATOR_FILTER='',CATEGORY_FILTER='',APPROVED='YES',REVIEW_NOTE='AUTO_EXACT_CODE_PROVISIONAL; validate before clinical use')
> # Write template only on first run, never overwrite user's reviewed edits.
> if(!file.exists(reviewed_mapping_file)) {
+   template<-candidates %>% arrange(PARAMCD,desc(EXACT_CODE),desc(N_RECORDS)) %>%
+     transmute(PARAMCD,DATASET,CODE_VAR,CODE,EVALUATOR_FILTER='',CATEGORY_FILTER='',APPROVED='NO',REVIEW_NOTE=paste0('CANDIDATE ONLY: ',LABEL))
+   write_csv(template,reviewed_mapping_file,na='')
+ }
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
 
 Error in open.connection(file, "wb") : cannot open the connection > manual<-readr::read_csv(reviewed_mapping_file,col_types=readr::cols(.default=readr::col_character())) %>%
+   filter(toupper(trimws(APPROVED))=='YES') %>%
+   select(PARAMCD,DATASET,CODE_VAR,CODE,EVALUATOR_FILTER,CATEGORY_FILTER,APPROVED,REVIEW_NOTE)
Error: '/domino/vega_load2388_ard/05_reviewed_mapping_template.csv' does not exist.
> # Manual approved mapping replaces provisional automatic mapping for the same target.
> accepted<-bind_rows(auto %>% filter(!PARAMCD %in% manual$PARAMCD),manual) %>%
+   mutate(across(c(PARAMCD,DATASET,CODE_VAR,CODE),toupper))
Error: Problem with `filter()` input `..1`.
ℹ Input `..1` is `!PARAMCD %in% manual$PARAMCD`.
x object 'manual' not found
Run `rlang::last_error()` to see where the error occurred.
> # One approved rule per target, to avoid silently combining readers/codes.
> if(anyDuplicated(accepted$PARAMCD))stop('Multiple approved mappings for a PARAMCD; resolve in template first')
Error in anyDuplicated(accepted$PARAMCD) : object 'accepted' not found
> write_csv(accepted,file.path(output_dir,'07_mapping_rules_used.csv'),na='')
Error in is.data.frame(x) : object 'accepted' not found
> 
> # Candidate traceability, including evaluator and visit. A candidate is not a confirmed endpoint.
> key_candidates<-candidates %>% distinct(PARAMCD,DATASET,CODE_VAR,CODE)
> all_candidate_records<-obs %>% inner_join(key_candidates,by=c('DATASET','CODE_VAR','CODE')) %>%
+   filter(nzchar(VALUE))
> write_csv(all_candidate_records,file.path(output_dir,'08_candidate_traceability_long.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/08_candidate_traceability_long.csv': No such file or directory
> candidate_qc<-all_candidate_records %>% group_by(PARAMCD,DATASET,CODE,EVALUATOR,EVALUATOR_ID,AVISIT,AVISITN) %>%
+   summarise(N_RECORDS=n(),N_SUBJECTS=n_distinct(USUBJID),N_VALUES=n_distinct(VALUE),.groups='drop')
> write_csv(candidate_qc,file.path(output_dir,'09_candidate_coverage_by_visit_reader.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/09_candidate_coverage_by_visit_reader.csv': No such file or directory
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
> # Add observed visits not present in SV, but report them separately.
> observed_grid<-obs %>% filter(nzchar(USUBJID),nzchar(AVISIT)|!is.na(AVISITN)) %>% distinct(USUBJID,AVISIT,AVISITN)
> missing_from_sv<-if(grid_source=='SV')anti_join(observed_grid,grid,by=c('USUBJID','AVISIT','AVISITN')) else tibble()
> write_csv(missing_from_sv,file.path(output_dir,'11_visits_not_in_sv.csv'),na='')
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
  cannot open file '/domino/vega_load2388_ard/11_visits_not_in_sv.csv': No such file or directory
> # Union ensures observed results are not lost because of mismatched visit labels.
> grid<-bind_rows(grid,observed_grid) %>% distinct() %>% arrange(USUBJID,AVISITN,AVISIT)
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
Error in open.connection(file, "wb") : cannot open the connection
In addition: Warning message:
In open.connection(file, "wb") :
 
 Error in open.connection(file, "wb") : cannot open the connection > 
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
Error in nrow(ard) : object 'ard' not found
> cat('\nFINISHED: ',output_dir,'\n',sep='')

FINISHED: /domino/vega_load2388_ard
> print(summary %>% count(STATUS))
Error in UseMethod("count") : 
  no applicable method for 'count' applied to an object of class "function"
> cat('ARD: ',nrow(ard),' rows x ',ncol(ard),' columns; ',n_distinct(ard$USUBJID),' subjects\n',sep='')
Error in nrow(ard) : object 'ard' not found
> cat('Review 05_reviewed_mapping_template.csv and rerun after approving mappings.\n')
Review 05_reviewed_mapping_template.csv and rerun after approving mappings.
> cat('CAUTION: provisional SDTM ARD is not equivalent to ADaM estimand-derived ARD.\n')
CAUTION: provisional SDTM ARD is not equivalent to ADaM estimand-derived ARD.
