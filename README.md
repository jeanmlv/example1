# example1

def ordered_visits(variable_df: pd.DataFrame) -> list[str]:
    """Return visit labels using AVISIT_ORDER as the preferred clinical order."""
    if "AVISIT" not in variable_df.columns:
        return []

    work = variable_df.loc[variable_df["AVISIT"].notna()].copy()
    if work.empty:
        return []

    work["AVISIT"] = work["AVISIT"].astype(str)

    # Preferred ordering: AVISIT_ORDER
    # Examples:
    # 2001-WEEK I-0 BASELINE
    # 3008-WEEK M-8
    # 3052-WEEK M-52
    if "AVISIT_ORDER" in work.columns:
        order = (
            work["AVISIT_ORDER"]
            .astype("string")
            .str.extract(r"^\s*(\d+)", expand=False)
        )

        order = pd.to_numeric(order, errors="coerce")

        if order.notna().any():
            work["_order"] = order

            return (
                work[["AVISIT", "_order"]]
                .dropna(subset=["_order"])
                .groupby("AVISIT", as_index=False)["_order"]
                .min()
                .sort_values(["_order", "AVISIT"])["AVISIT"]
                .tolist()
            )

    # Secondary ordering: AVISITN
    if "AVISITN" in work.columns:
        order = pd.to_numeric(work["AVISITN"], errors="coerce")

        if order.notna().any():
            work["_order"] = order

            return (
                work[["AVISIT", "_order"]]
                .groupby("AVISIT", as_index=False)["_order"]
                .min()
                .sort_values(["_order", "AVISIT"])["AVISIT"]
                .tolist()
            )

    # Final fallback
    return sorted(work["AVISIT"].dropna().unique().tolist())
