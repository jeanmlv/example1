# example1

sdtm_available = len(
    get_locations(df, "SDTM/ADaM Location")
)

ard_available = len(
    get_locations(df, "ARD Location")
)

annotations_available = len(
    get_locations(df, "Annotations Location")
)

clinical_gt_available = len(
    get_locations(df, "Clinical GT Location")
)

feature_vectors_available = len(
    get_locations(df, "Feature Vectors Location")
)
