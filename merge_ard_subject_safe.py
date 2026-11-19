"""CSV-only ARD merge with subject-level ADSL_AGE deduplication.

- Input priority is FILES_TO_MERGE order (newest first).
- Exact four-key matches merge distinct cell values with ' | '.
- Incomplete keys stay separate; no unsafe matching of event/parameter records.
- ADSL_AGE is moved to subject level and written on ONE output row per USUBJID.
- Different ages are retained in SUBJECT_AGE_CONFLICTS.csv and concatenated
  in SUBJECTS.csv; main ARD keeps first-file-first age for numeric usability.
- No rows or non-AGE cells are discarded just to reach 840.
- Uses disk-backed SQLite and Python standard library only.
"""
from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import time
from pathlib import Path

INPUT_FOLDER = Path(r"C:\Users\JMende95\OneDrive - JNJ\Desktop\ard_data\csv")
FILES_TO_MERGE = [
    "78934804UCO2001_duet_uc_wk96_ard_20261119.csv",
    "78934804UCO2001_duet_uc_wk48_ard_20260617.csv",
]
OUTPUT_FOLDER = INPUT_FOLDER / "merged_subject_safe"
KEYS = ("USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER")
AGE_COL = "ADSL_AGE"
SEPARATOR = " | "
BATCH_ROWS = 1000
PROGRESS_EVERY = 2000
KEEP_SQLITE = False
MIN_FREE_GB = 2


def norm(value):
    return "" if value is None else str(value).strip()


def distinct_merge(old, new):
    if not old:
        return new, False
    if not new or old == new:
        return old, False
    parts = [p.strip() for p in old.split(SEPARATOR) if p.strip()]
    changed = False
    for part in new.split(SEPARATOR):
        part = part.strip()
        if part and part not in parts:
            parts.append(part)
            changed = True
    return SEPARATOR.join(parts), changed


def main():
    started = time.monotonic()
    paths = [INPUT_FOLDER / name for name in FILES_TO_MERGE]
    for p in paths:
        if not p.is_file() or p.suffix.lower() != ".csv":
            raise FileNotFoundError(f"CSV not found: {p}")
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(OUTPUT_FOLDER).free < MIN_FREE_GB * 1024**3:
        raise RuntimeError(f"Less than {MIN_FREE_GB} GiB free")
    db_path = OUTPUT_FOLDER / "merge_working.sqlite"
    if db_path.exists():
        raise FileExistsError(f"Working DB already exists: {db_path}")

    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA cache_size=-65536")
    db.execute("CREATE TABLE records (rid TEXT PRIMARY KEY, payload TEXT NOT NULL, seq INTEGER NOT NULL) WITHOUT ROWID")
    db.execute("CREATE TABLE subjects (subj TEXT PRIMARY KEY, first_age TEXT, all_ages TEXT, age_count INTEGER NOT NULL) WITHOUT ROWID")
    columns = list(KEYS)
    stats = []
    seq = 0
    success = False
    try:
        with (OUTPUT_FOLDER / "VALUE_CONFLICTS.csv").open("w", encoding="utf-8-sig", newline="") as fc, \
             (OUTPUT_FOLDER / "DUPLICATE_KEYS.csv").open("w", encoding="utf-8-sig", newline="") as fd, \
             (OUTPUT_FOLDER / "INCOMPLETE_KEYS.csv").open("w", encoding="utf-8-sig", newline="") as fi, \
             (OUTPUT_FOLDER / "SUBJECT_AGE_CONFLICTS.csv").open("w", encoding="utf-8-sig", newline="") as fa:
            wc, wd, wi, wa = map(csv.writer, (fc, fd, fi, fa))
            wc.writerow(["INCOMING_FILE", *KEYS, "COLUMN", "PREVIOUS_VALUE", "INCOMING_VALUE", "MERGED_VALUE"])
            wd.writerow(["FILE", "ROW_NUMBER", *KEYS])
            wi.writerow(["FILE", "ROW_NUMBER", *KEYS, "MISSING_KEYS"])
            wa.writerow(["FILE", "ROW_NUMBER", "USUBJID", "FIRST_AGE", "INCOMING_AGE", "ALL_AGES"])
            for file_no, path in enumerate(paths, 1):
                n = duplicates = incomplete = conflicts = age_conflicts = 0
                seen_this_file = set()
                print(f"[{file_no}/{len(paths)}] {path.name}", flush=True)
                with path.open("r", encoding="utf-8-sig", newline="", buffering=1024 * 1024) as fh:
                    reader = csv.reader(fh)
                    try:
                        headers = [norm(v) for v in next(reader)]
                    except StopIteration as exc:
                        raise ValueError(f"Empty CSV: {path}") from exc
                    if not all(headers) or len(headers) != len(set(headers)):
                        raise ValueError(f"Blank or repeated headers in {path.name}")
                    if not set(KEYS).issubset(headers):
                        raise ValueError(f"Missing keys in {path.name}: {set(KEYS) - set(headers)}")
                    for c in headers:
                        if c not in columns:
                            columns.append(c)
                    key_idx = [headers.index(k) for k in KEYS]
                    age_idx = headers.index(AGE_COL) if AGE_COL in headers else None
                    other_idx = [(i, c) for i, c in enumerate(headers) if c not in KEYS and c != AGE_COL]
                    db.execute("BEGIN")
                    for line_no, row in enumerate(reader, 2):
                        if len(row) != len(headers):
                            raise ValueError(f"{path.name}:{line_no}: {len(row)} cells, expected {len(headers)}")
                        if not any(norm(v) for v in row):
                            continue
                        n += 1
                        seq += 1
                        keys = tuple(norm(row[i]) for i in key_idx)
                        subj = keys[0]
                        age = norm(row[age_idx]) if age_idx is not None else ""
                        if subj:
                            previous = db.execute("SELECT first_age,all_ages,age_count FROM subjects WHERE subj=?", (subj,)).fetchone()
                            if previous is None:
                                db.execute("INSERT INTO subjects VALUES (?,?,?,?)", (subj, age, age, int(bool(age))))
                            elif age:
                                first_age, all_ages, age_count = previous
                                merged_age, changed = distinct_merge(all_ages or "", age)
                                if changed:
                                    age_conflicts += 1
                                    wa.writerow([path.name, line_no, subj, first_age, age, merged_age])
                                if changed or not first_age:
                                    db.execute("UPDATE subjects SET first_age=?, all_ages=?, age_count=? WHERE subj=?",
                                               (first_age or age, merged_age, age_count + int(changed), subj))
                        elif age:
                            wi.writerow([path.name, line_no, *keys, "USUBJID;AGE_UNASSIGNABLE"])
                        if all(keys):
                            rid = "K" + json.dumps(keys, ensure_ascii=False, separators=(",", ":"))
                            if rid in seen_this_file:
                                duplicates += 1
                                wd.writerow([path.name, line_no, *keys])
                            else:
                                seen_this_file.add(rid)
                        else:
                            incomplete += 1
                            wi.writerow([path.name, line_no, *keys, ";".join(k for k, v in zip(KEYS, keys) if not v)])
                            rid = f"I{file_no}:{line_no}"
                        incoming = {c: norm(row[i]) for i, c in other_idx if norm(row[i])}
                        existing = db.execute("SELECT payload FROM records WHERE rid=?", (rid,)).fetchone()
                        if existing is None:
                            payload = dict(zip(KEYS, keys))
                            payload.update(incoming)
                            db.execute("INSERT INTO records VALUES (?,?,?)",
                                       (rid, json.dumps(payload, ensure_ascii=False, separators=(",", ":")), seq))
                        else:
                            payload = json.loads(existing[0])
                            modified = False
                            for c, val in incoming.items():
                                old = payload.get(c, "")
                                merged, changed = distinct_merge(old, val)
                                if old != merged:
                                    payload[c] = merged
                                    modified = True
                                if changed:
                                    conflicts += 1
                                    wc.writerow([path.name, *keys, c, old, val, merged])
                            if modified:
                                db.execute("UPDATE records SET payload=? WHERE rid=?",
                                           (json.dumps(payload, ensure_ascii=False, separators=(",", ":")), rid))
                        if n % BATCH_ROWS == 0:
                            db.commit()
                            db.execute("BEGIN")
                        if n % PROGRESS_EVERY == 0:
                            print(f"  {n:,} input rows", flush=True)
                    db.commit()
                stats.append([path.name, n, len(headers), duplicates, incomplete, conflicts, age_conflicts])
                print(f"  Done: {n:,} rows; {duplicates:,} duplicate keys; {incomplete:,} incomplete keys", flush=True)

        # Stream merged rows; first appearance of each subject receives ADSL_AGE.
        # Age does not appear on other rows, so filtering populated AGE yields one row per subject.
        if AGE_COL not in columns:
            columns.append(AGE_COL)
        seen_age_subjects = set()
        out_rows = populated_age_rows = 0
        with (OUTPUT_FOLDER / "MERGED_ARD.csv").open("w", encoding="utf-8-sig", newline="", buffering=1024 * 1024) as fh:
            writer = csv.writer(fh)
            writer.writerow(columns)
            for (raw,) in db.execute("SELECT payload FROM records ORDER BY seq"):
                payload = json.loads(raw)
                subj = payload.get("USUBJID", "")
                if subj and subj not in seen_age_subjects:
                    # Only mark seen if an age actually exists.
                    subject_row = db.execute("SELECT first_age FROM subjects WHERE subj=?", (subj,)).fetchone()
                    age = subject_row[0] if subject_row else ""
                    if age:
                        payload[AGE_COL] = age
                        seen_age_subjects.add(subj)
                        populated_age_rows += 1
                writer.writerow([payload.get(c, "") for c in columns])
                out_rows += 1
                if out_rows % PROGRESS_EVERY == 0:
                    print(f"  Exported {out_rows:,} rows", flush=True)

        with (OUTPUT_FOLDER / "SUBJECTS.csv").open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["USUBJID", "ADSL_AGE_PRIMARY", "ADSL_AGE_ALL_VALUES", "DISTINCT_AGE_COUNT"])
            for row in db.execute("SELECT subj,first_age,all_ages,age_count FROM subjects ORDER BY subj"):
                w.writerow(row)
        with (OUTPUT_FOLDER / "FILE_COMPARISON.csv").open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["FILE", "INPUT_ROWS", "COLUMNS", "DUPLICATE_KEY_ROWS", "INCOMPLETE_KEY_ROWS", "VALUE_CONFLICT_EVENTS", "AGE_CONFLICT_EVENTS"])
            w.writerows(stats)
        subject_total, subjects_with_age = db.execute("SELECT COUNT(*),SUM(CASE WHEN first_age<>'' THEN 1 ELSE 0 END) FROM subjects").fetchone()
        with (OUTPUT_FOLDER / "SUMMARY.csv").open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["METRIC", "VALUE"])
            w.writerows([
                ("Output rows", out_rows),
                ("Output columns", len(columns)),
                ("Unique USUBJID", subject_total),
                ("USUBJID with ADSL_AGE", subjects_with_age or 0),
                ("Rows with ADSL_AGE in merged CSV", populated_age_rows),
                ("Duplicate complete keys", sum(s[3] for s in stats)),
                ("Incomplete keys", sum(s[4] for s in stats)),
                ("Non-age conflict events", sum(s[5] for s in stats)),
                ("Age conflict events", sum(s[6] for s in stats)),
                ("Elapsed seconds", round(time.monotonic() - started, 1)),
            ])
        print(f"SUCCESS: {out_rows:,} rows; {subject_total:,} subjects; {populated_age_rows:,} rows with ADSL_AGE", flush=True)
        print(f"Output: {OUTPUT_FOLDER / 'MERGED_ARD.csv'}", flush=True)
        success = True
    finally:
        db.close()
        if success and not KEEP_SQLITE:
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
