# example1

# Mean ARD coverage: consider only studies with >= 1% coverage
coverage = pd.to_numeric(
    ard.get("Coverage %", pd.Series(dtype=float)),
    errors="coerce"
)

valid_coverage = coverage[coverage >= 1]

avg = valid_coverage.mean()

c5.metric(
    "Mean ARD coverage",
    f"{avg:.0f}%" if pd.notna(avg) else "—"
)




# Mean coverage: consider only studies with >= 1% coverage
coverage = pd.to_numeric(
    a.get("Coverage %", pd.Series(dtype=float)),
    errors="coerce"
)

valid_coverage = coverage[coverage >= 1]

avg = valid_coverage.mean()

c4.metric(
    "Mean coverage",
    f"{avg:.0f}%" if pd.notna(avg) else "—"
)
