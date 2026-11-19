"""Fast, loss-aware CSV ARD merge. Python standard library only.

Same four-key, first-file-first, distinct-value concatenation rules as legacy merge.
Incomplete keys are never matched. Duplicate complete keys are merged and reported.
Output is an inventory/coverage dataset, NOT automatically analysis-ready.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import sqlite3
import time
from collections import Counter
from pathlib import Path

# ========================== CONFIGURATION ==========================
INPUT_FOLDER = Path(r"C:\Users\JMende95\OneDrive - JNJ\Desktop\ard_data\csv")
FILES_TO_MERGE = [
    "78934804UCO2001_duet_uc_wk96_ard_20261119.csv",  # newest FIRST
    "78934804UCO2001_duet_uc_wk48_ard_20260617.csv",
]
OUTPUT_FOLDER = INPUT_FOLDER / "merged_fast"
KEYS = ("USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER")
SEPARATOR = " | "
BATCH_ROWS = 1000  # commit interval
PROGRESS_EVERY = 1000
KEEP_SQLITE = False
MIN_FREE_GB = 2
# ==================================================================


def normalize(value: str | None) -> str:
    return "" if value is None else str(value).strip()


def distinct_merge(old: str, new: str) -> tuple[str, bool]:
    """Matches the legacy distinct_merge behavior (including existing ' | ' values)."""
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


def write_csv_row(writer, record):
    writer.writerow(record)


def main():
    start = time.monotonic()
    if len(FILES_TO_MERGE) < 2:
        raise ValueError("Configure at least two CSV files")
    paths = [INPUT_FOLDER / f for f in FILES_TO_MERGE]
    for p in paths:
        if p.suffix.lower() != ".csv" or not p.is_file():
            raise FileNotFoundError(f"CSV not found: {p}")
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(OUTPUT_FOLDER).free < MIN_FREE_GB * 1024**3:
        raise RuntimeError(f"Less than {MIN_FREE_GB} GiB available")

    # One JSON document per matched row, rather than one SQLite record per cell.
    # Dramatically reduces index updates and random disk access on wide ARDs.
    db_path = OUTPUT_FOLDER / "merge_working.sqlite"
    if db_path.exists():
        raise FileExistsError(f"Working database already exists: {db_path}. Remove only after checking it is not needed.")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-32768")
    conn.execute("CREATE TABLE records (rid TEXT PRIMARY KEY, payload TEXT NOT NULL, first_seq INTEGER NOT NULL) WITHOUT ROWID")
    # Separate key values in payload; rid is a JSON serialization of keys to avoid hash collisions.
    columns = list(KEYS)
    stats = []
    seq = 0
    completed = False
    try:
        with (OUTPUT_FOLDER / "VALUE_CONFLICTS.csv").open("w", encoding="utf-8-sig", newline="") as f_conf, \
             (OUTPUT_FOLDER / "DUPLICATE_KEYS.csv").open("w", encoding="utf-8-sig", newline="") as f_dup, \
             (OUTPUT_FOLDER / "INCOMPLETE_KEYS.csv").open("w", encoding="utf-8-sig", newline="") as f_inc:
            wc, wd, wi = csv.writer(f_conf), csv.writer(f_dup), csv.writer(f_inc)
            wc.writerow(["INCOMING_FILE", *KEYS, "COLUMN", "PREVIOUS_VALUE", "INCOMING_VALUE", "MERGED_VALUE"])
            wd.writerow(["FILE", *KEYS, "ROW_NUMBER"])
            wi.writerow(["FILE", "ROW_NUMBER", *KEYS, "MISSING_KEYS"])
            for file_no, path in enumerate(paths, 1):
                count = dup = incomplete = conflicts = 0
                seen_this_file = set()  # memory proportional to unique complete keys
                print(f"[{file_no}/{len(paths)}] Reading {path.name}", flush=True)
                with path.open("r", encoding="utf-8-sig", newline="", buffering=1024*1024) as f:
                    reader = csv.reader(f)
                    try:
                        headers = [normalize(h) for h in next(reader)]
                    except StopIteration as e:
                        raise ValueError(f"Empty CSV: {path}") from e
                    if not all(headers) or len(set(headers)) != len(headers):
                        raise ValueError(f"Blank or repeated column names: {path.name}")
                    missing = set(KEYS) - set(headers)
                    if missing:
                        raise ValueError(f"{path.name} missing keys: {sorted(missing)}")
                    for col in headers:
                        if col not in columns:
                            columns.append(col)
                    key_idx = [headers.index(k) for k in KEYS]
                    nonkey = [(i, c) for i, c in enumerate(headers) if c not in KEYS]
                    conn.execute("BEGIN")
                    for line_no, row in enumerate(reader, 2):
                        if not any(normalize(v) for v in row):
                            continue
                        if len(row) != len(headers):
                            raise ValueError(f"{path.name} row {line_no}: {len(row)} cells, expected {len(headers)}")
                        count += 1
                        seq += 1
                        keys = tuple(normalize(row[i]) for i in key_idx)
                        complete = all(keys)
                        if complete:
                            rid = "K" + json.dumps(keys, ensure_ascii=False, separators=(",", ":"))
                            if rid in seen_this_file:
                                dup += 1
                                wd.writerow([path.name, *keys, line_no])
                            else:
                                seen_this_file.add(rid)
                        else:
                            incomplete += 1
                            wi.writerow([path.name, line_no, *keys, ";".join(k for k, v in zip(KEYS, keys) if not v)])
                            # Incomplete keys are intentionally unique, including across files.
                            rid = "I" + json.dumps([file_no, line_no], separators=(",", ":"))
                        incoming = {col: normalize(row[i]) for i, col in nonkey if normalize(row[i])}
                        found = conn.execute("SELECT payload FROM records WHERE rid=?", (rid,)).fetchone()
                        if found is None:
                            payload = {**dict(zip(KEYS, keys)), **incoming}
                            conn.execute("INSERT INTO records(rid,payload,first_seq) VALUES(?,?,?)",
                                         (rid, json.dumps(payload, ensure_ascii=False, separators=(",", ":")), seq))
                        else:
                            payload = json.loads(found[0])
                            changed_any = False
                            for col, val in incoming.items():
                                old = payload.get(col, "")
                                if not old:
                                    payload[col] = val
                                    changed_any = True
                                else:
                                    merged, changed = distinct_merge(old, val)
                                    if changed:
                                        wc.writerow([path.name, *keys, col, old, val, merged])
                                        conflicts += 1
                                        payload[col] = merged
                                        changed_any = True
                            if changed_any:
                                conn.execute("UPDATE records SET payload=? WHERE rid=?",
                                             (json.dumps(payload, ensure_ascii=False, separators=(",", ":")), rid))
                        if count % BATCH_ROWS == 0:
                            conn.commit()
                            conn.execute("BEGIN")
                        if count % PROGRESS_EVERY == 0:
                            print(f"  {count:,} rows processed; {conflicts:,} conflicts", flush=True)
                    conn.commit()
                stats.append((path.name, count, len(headers), dup, incomplete, conflicts))
                print(f"  Done: {count:,} rows, {dup:,} duplicate keys, {incomplete:,} incomplete keys, {conflicts:,} conflicts", flush=True)

        # Keep only the needed final CSV, avoid expensive XLSX generation.
        merged_path = OUTPUT_FOLDER / "MERGED_ARD.csv"
        with merged_path.open("w", encoding="utf-8-sig", newline="", buffering=1024*1024) as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            exported = 0
            populated = 0
            # Sorted by first occurrence; uses SQLite temp index only during export.
            for (payload_json,) in conn.execute("SELECT payload FROM records ORDER BY first_seq"):
                payload = json.loads(payload_json)
                writer.writerow([payload.get(col, "") for col in columns])
                exported += 1
                populated += sum(bool(v) for v in payload.values())
                if exported % PROGRESS_EVERY == 0:
                    print(f"  Exported {exported:,} rows", flush=True)
        with (OUTPUT_FOLDER / "FILE_COMPARISON.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["FILE", "INPUT_ROWS", "COLUMNS", "DUPLICATE_KEY_ROWS", "INCOMPLETE_KEY_ROWS", "CONFLICT_EVENTS"])
            w.writerows(stats)
        with (OUTPUT_FOLDER / "SUMMARY.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["METRIC", "VALUE"])
            w.writerows([
                ("Output rows", exported),
                ("Populated cells", populated),
                ("Conflict events", sum(x[5] for x in stats)),
                ("Duplicate key rows", sum(x[3] for x in stats)),
                ("Incomplete key rows", sum(x[4] for x in stats)),
                ("Output columns", len(columns)),
                ("Elapsed seconds", round(time.monotonic()-start, 1)),
            ])
        print(f"SUCCESS: {exported:,} rows, {len(columns):,} columns. Output: {merged_path}", flush=True)
        print(f"Elapsed: {(time.monotonic()-start)/60:.1f} min", flush=True)
        completed = True
    finally:
        conn.close()
        if completed and not KEEP_SQLITE:
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
