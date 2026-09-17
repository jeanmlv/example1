# example1

Yes, that's expected. DATA_SPLIT_DETAILS is at the detailed subject/video level, so GALAXI can have many rows there. DATA_SPLITS is intended to be a summary of those records, so we should not copy all the rows from DATA_SPLIT_DETAILS.

For DATA_SPLITS, we should create one row for each unique split configuration available in DATA_SPLIT_DETAILS, based mainly on Dataset Role, CV Fold, and Split Label. Then we can summarize the number of patients/videos associated with each split.

So, for example, if GALAXI has many subjects assigned to dev_fold0, they would appear as multiple rows in DATA_SPLIT_DETAILS, but only one summarized row for dev_fold0 in DATA_SPLITS.

For fields that are not available in the source data, we can leave them blank for now rather than trying to infer them.
