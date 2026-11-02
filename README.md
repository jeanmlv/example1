# example1

# Preserve all generated columns without selecting nonexistent names.
raw = raw.reset_index(drop=True)
processed = processed.reset_index(drop=True)

# Display available columns for validation.
print("RAW columns:", raw.columns.tolist())
print("PROCESSED columns:", processed.columns.tolist())
