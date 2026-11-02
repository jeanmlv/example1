# example1


from pathlib import Path
import pandas as pd
import re

source = Path("video_inventory_output_anthem/all_video_inventory.csv")
target = Path("video_inventory_output_anthem/all_video_inventory_corrected.csv")

df = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8-sig")

def parse_anthem_path(path):
    parts = str(path).replace("\\", "/").split("/")

    site = ""
    patient = ""
    visit = ""

    for i, part in enumerate(parts):
        if re.match(r"(?i)^SITE\s+", part):
            site = re.sub(r"(?i)^SITE\s+", "", part).strip()

            if i + 1 < len(parts):
                patient = parts[i + 1].strip()

            if i + 2 < len(parts):
                visit = parts[i + 2].strip()

            break

    return pd.Series([site, patient, visit])

mask = df["data_type"].eq("processed")

parsed = df.loc[mask, "relative_path"].apply(parse_anthem_path)
parsed.columns = ["site", "patient_id", "visit"]

df.loc[mask, ["site", "patient_id", "visit"]] = parsed.to_numpy()

df.to_csv(target, index=False, encoding="utf-8-sig")

print("Corrected inventory:", target)
print("Processed video items:", mask.sum())
print(
    "Unique patients:",
    df.loc[mask & df["patient_id"].ne(""), ["site", "patient_id"]]
      .drop_duplicates()
      .shape[0]
)
print("Visits:", sorted(df.loc[mask, "visit"].unique()))
print("Missing patient IDs:", ((mask) & df["patient_id"].eq("")).sum())
