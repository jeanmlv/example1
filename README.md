# example1

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Observations", f"{len(variable_df):,}")

c2.metric(
    "Subjects",
    f"{variable_df['USUBJID'].nunique():,}"
    if "USUBJID" in variable_df.columns
    else "—"
)

c3.metric(
    "Visits",
    f"{variable_df['AVISIT'].nunique():,}"
    if "AVISIT" in variable_df.columns
    else "—"
)

c4.metric(
    "Mean",
    f"{variable_df['VALUE_NUM'].mean():.2f}"
)

c5.metric(
    "Median",
    f"{variable_df['VALUE_NUM'].median():.2f}"
)
