# VEGA load-2388: evidence-only clinical mapping validation
# No automatic approval or endpoint derivation. Writes to /mnt.
CONFIG <- list(
  input_dir = '/domino/datasets/local/clinical-trial-data/CNTO1959UCO2002-VEGA-WK50/load-2388/Data/csv',
  output_dir = '/mnt/CNTO1959UCO2002_VEGA_load2388_validation'
)
stopifnot(dir.exists(CONFIG$input_dir))
dir.create(CONFIG$output_dir, recursive=TRUE, showWarnings=FALSE)
stopifnot(dir.exists(CONFIG$output_dir), file.access(CONFIG$output_dir,2)==0)
files <- list.files(CONFIG$input_dir, pattern='\\.csv$', recursive=TRUE, full.names=TRUE, ignore.case=TRUE)
files <- files[!grepl('/cleaned/',files,ignore.case=TRUE)]
domain <- function(f) toupper(sub('\\..*$','',basename(f)))
files <- files[domain(files) %in% c('MO','SUPPMO','MI','SUPPMI','QS','SUPPQS','LB','SUPPLB','ZR','CM','FA','SV')]
if(any(duplicated(domain(files)))) stop('Duplicate domain files detected: ',paste(unique(domain(files)[duplicated(domain(files))]),collapse=', '))
read_domain <- function(f) {
  x <- tryCatch(read.csv(f,stringsAsFactors=FALSE,check.names=FALSE,na.strings=c('','NA'),colClasses='character'),error=function(e)stop('Failed to read ',f,': ',conditionMessage(e)))
  names(x) <- toupper(names(x)); x
}
write_out <- function(x,name) write.csv(x,file.path(CONFIG$output_dir,name),row.names=FALSE,na='')
report <- list(); detail <- list(); supp <- list(); inv <- list()
for(f in files){
 d <- domain(f); x <- read_domain(f)
 inv[[length(inv)+1]] <- data.frame(DOMAIN=d,ROWS=nrow(x),COLUMNS=ncol(x),SOURCE=f)
 codevar <- paste0(d,'TESTCD'); labelvar <- paste0(d,'TEST'); valcols <- intersect(c(paste0(d,c('STRESN','STRESC','ORRES')), 'VISIT','VISITNUM','USUBJID',paste0(d,'SEQ'),'MOEVAL','MOCAT','MOSCAT','LBSTRESU','LBORRESU','MIEVAL','QSCAT'),names(x))
 if(codevar %in% names(x)){
   codes <- unique(x[[codevar]]); codes <- codes[!is.na(codes)]
   for(code in codes){
     z <- x[x[[codevar]]==code,,drop=FALSE]
     label <- if(labelvar %in% names(z)) paste(head(unique(na.omit(z[[labelvar]])),3),collapse=' | ') else ''
     report[[length(report)+1]] <- data.frame(DOMAIN=d,CODE=code,LABEL=label,N_RECORDS=nrow(z),N_SUBJECTS=if('USUBJID'%in%names(z))length(unique(na.omit(z$USUBJID))) else NA_integer_,SOURCE=f)
   }
   if(d %in% c('MO','MI','QS','LB')){
     # All observed TESTCDs, including unexpected codes; retain traceable evidence.
     detail[[length(detail)+1]] <- data.frame(DOMAIN=d,x[,unique(c('USUBJID','VISIT','VISITNUM',paste0(d,'SEQ'),codevar,labelvar,valcols))[unique(c('USUBJID','VISIT','VISITNUM',paste0(d,'SEQ'),codevar,labelvar,valcols)) %in% names(x)] ,drop=FALSE],check.names=FALSE)
   }
 }
 if(d %in% c('SUPPMO','SUPPMI','SUPPQS','SUPPLB')){
   keep <- intersect(c('USUBJID','IDVAR','IDVARVAL','QNAM','QLABEL','QVAL','QEVAL'),names(x))
   supp[[length(supp)+1]] <- data.frame(DOMAIN=d,x[,keep,drop=FALSE],check.names=FALSE)
 }
}
write_out(do.call(rbind,inv),'01_domains_loaded.csv')
if(length(report)) write_out(do.call(rbind,report),'02_all_testcd_coverage.csv')
if(length(detail)){
  # Align heterogeneous domains before row-binding.
  allcols <- unique(unlist(lapply(detail,names)))
  aligned <- lapply(detail,function(x){for(k in setdiff(allcols,names(x)))x[[k]]<-NA_character_;x[,allcols,drop=FALSE]})
  write_out(do.call(rbind,aligned),'03_observed_records_all_codes.csv')
}
if(length(supp)){
  allcols <- unique(unlist(lapply(supp,names)))
  aligned <- lapply(supp,function(x){for(k in setdiff(allcols,names(x)))x[[k]]<-NA_character_;x[,allcols,drop=FALSE]})
  write_out(do.call(rbind,aligned),'04_supplemental_qualifiers.csv')
}
cat('Completed evidence extraction in:',CONFIG$output_dir,'\n')
