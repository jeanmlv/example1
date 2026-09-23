# example1

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Observations", f"{len(variable_df):,}")

k2.metric(
    "Subjects",
    f"{variable_df['USUBJID'].nunique():,}"
    if "USUBJID" in variable_df.columns
    else "—"
)

k3.metric(
    "Visits",
    f"{variable_df['AVISIT'].nunique():,}"
    if "AVISIT" in variable_df.columns
    else "—"
)

k4.metric(
    "Mean",
    f"{variable_df['VALUE_NUM'].mean():.2f}"
)

k5.metric(
    "Median",
    f"{variable_df['VALUE_NUM'].median():.2f}"
)
