# example1

[server]
maxUploadSize = 2048


k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Observations", f"{observations:,}")

k2.metric(
    "Subjects",
    f"{subjects:,}" if subjects is not None else "—"
)

k3.metric(
    "Visits",
    f"{len(visits):,}" if visits else "—"
)

if kind == "numeric":
    k4.metric(
        "Mean",
        f"{variable_df['VALUE'].mean():.2f}"
    )

    k5.metric(
        "Median",
        f"{variable_df['VALUE'].median():.2f}"
    )

    _render_numeric_explorer(
        variable_df,
        row["Variable"],
        visits
    )

else:
    k4.metric(
        "Categories",
        f"{variable_df['VALUE'].nunique():,}"
    )

    k5.metric(
        "Mode",
        (
            str(variable_df["VALUE"].mode().iloc[0])
            if not variable_df["VALUE"].mode().empty
            else "—"
        )
    )

    _render_categorical_explorer(
        variable_df,
        row["Variable"],
        visits
    )
