"""Compare an older and a newer ARD CSV without changing either file.

Python 3.10+; standard library only. Large-file friendly: SQLite on disk.
Run: python compare_ard_csv.py

IMPORTANT: Comparisons of individual values are made ONLY when all configured
keys are populated and identify exactly one row in EACH file. Ambiguous or
incomplete-key rows are reported, never silently matched or declared covered.
"""
from __future__ import annotations

import csv
import hashlib
import shutil
import sqlite3
import time
from collections import Counter
from pathlib import Path

# ========================== CONFIGURATION ==========================
INPUT_FOLDER = Path(r"C:\Users\JMende95\OneDrive - JNJ\Desktop\ard_data\csv")
OLD_FILE = "78934804UCO2001_duet_uc_wk48_ard_20260617.csv"
NEW_FILE = "78934804UCO2001_duet_uc_wk96_ard_20261119.csv"
OUTPUT_FOLDER = INPUT_FOLDER / "comparison_wk48_vs_wk96"
KEYS = ("USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER")
CSV_ENCODING = "utf-8-sig"  # change to 'cp1252' if source is Windows-encoded
BATCH_SIZE = 5000
MIN_FREE_GB = 2
KEEP_SQLITE = False
# ===================================================================


def normalize(value: str | None) -> str:
    """Trim external whitespace only. No case/date/numeric coercion."""
    return "" if value is None else value.strip()


def hash_key(values: tuple[str, ...]) -> str:
    # Length-prefixed encoding avoids delimiter collision.
    payload = "".join(f"{len(v)}:{v}" for v in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def open_csv(path: Path):
    # newline='' is essential for correct CSV parsing, including quoted newlines.
    return path.open("r", encoding=CSV_ENCODING, newline="")


def setup(db: sqlite3.Connection):
    db.executescript("""
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=NORMAL;
        PRAGMA temp_store=FILE;
        PRAGMA cache_size=-32768;
        CREATE TABLE records (
            src INTEGER NOT NULL, rn INTEGER NOT NULL, kh TEXT,
            subj TEXT, visit TEXT, visitn TEXT, visit_order TEXT,
            PRIMARY KEY(src,rn)
        ) WITHOUT ROWID;
        CREATE TABLE cells (
            src INTEGER NOT NULL, rn INTEGER NOT NULL,
            col TEXT NOT NULL, val TEXT NOT NULL,
            PRIMARY KEY(src,rn,col)
        ) WITHOUT ROWID;
        CREATE TABLE columns (src INTEGER, col TEXT, ordinal INTEGER,
            PRIMARY KEY(src,col)) WITHOUT ROWID;
    """)


def import_file(db: sqlite3.Connection, path: Path, src: int):
    stats = Counter()
    missing_by_key = Counter()
    patients = set()
    with open_csv(path) as handle:
        reader = csv.reader(handle)
        try:
            headers = [normalize(x) for x in next(reader)]
        except StopIteration:
            raise ValueError(f"Empty CSV: {path}")
        if not headers or any(not h for h in headers) or len(set(headers)) != len(headers):
            raise ValueError(f"Blank/duplicate headers in {path.name}")
        absent = set(KEYS) - set(headers)
        if absent:
            raise ValueError(f"{path.name} missing required key columns: {sorted(absent)}")
        indices = [headers.index(k) for k in KEYS]
        nonkey = [(i, h) for i, h in enumerate(headers) if h not in KEYS]
        db.executemany("INSERT INTO columns VALUES (?,?,?)", ((src, h, i) for i, h in enumerate(headers)))
        rec_batch, cell_batch = [], []
        for rn, row in enumerate(reader, start=2):
            if len(row) > len(headers):
                raise ValueError(f"{path.name}, CSV record starting near line {rn}: more fields than headers")
            if not row or all(not normalize(v) for v in row):
                continue
            keys = tuple(normalize(row[i]) if i < len(row) else "" for i in indices)
            complete = all(keys)
            kh = hash_key(keys) if complete else None
            if not complete:
                stats["incomplete_rows"] += 1
                for k, v in zip(KEYS, keys):
                    if not v:
                        missing_by_key[k] += 1
            if keys[0]:
                patients.add(keys[0])
            rec_batch.append((src, rn, kh, *keys))
            for idx, col in nonkey:
                val = normalize(row[idx]) if idx < len(row) else ""
                if val:
                    cell_batch.append((src, rn, col, val))
                    stats["populated_cells"] += 1
            stats["rows"] += 1
            if len(rec_batch) >= BATCH_SIZE:
                db.executemany("INSERT INTO records VALUES (?,?,?,?,?,?,?)", rec_batch)
                db.executemany("INSERT INTO cells VALUES (?,?,?,?)", cell_batch)
                db.commit()
                rec_batch.clear()
                cell_batch.clear()
                if stats["rows"] % 10000 < BATCH_SIZE:
                    print(f"  {path.name}: {stats['rows']:,} rows imported", flush=True)
        if rec_batch:
            db.executemany("INSERT INTO records VALUES (?,?,?,?,?,?,?)", rec_batch)
            db.executemany("INSERT INTO cells VALUES (?,?,?,?)", cell_batch)
        db.commit()
    stats["columns"] = len(headers)
    stats["patients"] = len(patients)
    return stats, missing_by_key


def csv_writer(path: Path, headers):
    handle = path.open("w", encoding="utf-8-sig", newline="")
    writer = csv.writer(handle)
    writer.writerow(headers)
    return handle, writer


def scalar(db, sql, args=()):
    return db.execute(sql, args).fetchone()[0]


def compare(db: sqlite3.Connection, output: Path, old_stats, new_stats, old_missing, new_missing):
    print("Building comparison indexes...", flush=True)
    db.executescript("""
        CREATE INDEX idx_records_key ON records(src,kh);
        CREATE INDEX idx_cells_column ON cells(src,col);
        CREATE TABLE groups AS
          SELECT kh,
            SUM(CASE WHEN src=1 THEN 1 ELSE 0 END) AS old_n,
            SUM(CASE WHEN src=2 THEN 1 ELSE 0 END) AS new_n
          FROM records WHERE kh IS NOT NULL GROUP BY kh;
        CREATE UNIQUE INDEX idx_groups ON groups(kh);
        CREATE TABLE pairs AS
          SELECT o.rn AS old_rn, n.rn AS new_rn, o.kh AS kh,
                 o.subj AS subj, o.visit AS visit,
                 o.visitn AS visitn, o.visit_order AS visit_order
          FROM groups g
          JOIN records o ON o.kh=g.kh AND o.src=1
          JOIN records n ON n.kh=g.kh AND n.src=2
          WHERE g.old_n=1 AND g.new_n=1;
        CREATE UNIQUE INDEX idx_pairs_old ON pairs(old_rn);
        CREATE UNIQUE INDEX idx_pairs_new ON pairs(new_rn);
    """)
    summary = Counter()
    summary["old_rows"] = old_stats["rows"]
    summary["new_rows"] = new_stats["rows"]
    summary["old_columns"] = old_stats["columns"]
    summary["new_columns"] = new_stats["columns"]
    summary["old_patients"] = old_stats["patients"]
    summary["new_patients"] = new_stats["patients"]
    summary["old_incomplete_key_rows"] = old_stats["incomplete_rows"]
    summary["new_incomplete_key_rows"] = new_stats["incomplete_rows"]
    summary["old_populated_cells"] = old_stats["populated_cells"]
    summary["new_populated_cells"] = new_stats["populated_cells"]
    summary["uniquely_matched_rows"] = scalar(db, "SELECT COUNT(*) FROM pairs")
    summary["old_complete_key_rows_not_uniquely_matched"] = scalar(db,
        "SELECT COUNT(*) FROM records r LEFT JOIN pairs p ON p.old_rn=r.rn WHERE r.src=1 AND r.kh IS NOT NULL AND p.old_rn IS NULL")
    summary["old_keys_absent_in_new"] = scalar(db,
        "SELECT COUNT(*) FROM groups WHERE old_n>0 AND new_n=0")
    summary["old_rows_in_keys_absent_in_new"] = scalar(db,
        "SELECT COALESCE(SUM(old_n),0) FROM groups WHERE old_n>0 AND new_n=0")
    summary["ambiguous_keys_in_either_file"] = scalar(db,
        "SELECT COUNT(*) FROM groups WHERE (old_n>1 OR new_n>1) AND old_n>0")
    summary["old_patients_absent_in_new"] = scalar(db, """
        SELECT COUNT(*) FROM (SELECT DISTINCT subj FROM records WHERE src=1 AND subj<>'') a
        WHERE NOT EXISTS (SELECT 1 FROM records b WHERE b.src=2 AND b.subj=a.subj)
    """)
    summary["old_patient_visits_absent_in_new"] = scalar(db, """
        SELECT COUNT(*) FROM (SELECT DISTINCT subj,visit,visitn FROM records
          WHERE src=1 AND subj<>'' AND visit<>'' AND visitn<>'') a
        WHERE NOT EXISTS (SELECT 1 FROM records b WHERE b.src=2
          AND b.subj=a.subj AND b.visit=a.visit AND b.visitn=a.visitn)
    """)

    with (output / "COLUMN_COVERAGE.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["COLUMN", "IN_OLD", "IN_NEW", "STATUS"])
        oldcols = {r[0] for r in db.execute("SELECT col FROM columns WHERE src=1")}
        newcols = {r[0] for r in db.execute("SELECT col FROM columns WHERE src=2")}
        for col in sorted(oldcols | newcols):
            a, b = col in oldcols, col in newcols
            w.writerow([col, int(a), int(b), "BOTH" if a and b else "OLD_ONLY" if a else "NEW_ONLY"])
        summary["old_columns_absent_in_new"] = len(oldcols - newcols)
        summary["new_columns_absent_in_old"] = len(newcols - oldcols)

    handle, writer = csv_writer(output / "KEY_COVERAGE.csv",
        ["USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER", "OLD_ROWS", "NEW_ROWS", "STATUS"])
    try:
        for kh, on, nn in db.execute("SELECT kh,old_n,new_n FROM groups WHERE old_n>0 AND (new_n=0 OR old_n>1 OR new_n>1)"):
            key = db.execute("SELECT subj,visit,visitn,visit_order FROM records WHERE src=1 AND kh=? LIMIT 1", (kh,)).fetchone()
            writer.writerow([*key, on, nn, "ABSENT_IN_NEW" if nn == 0 else "AMBIGUOUS_DUPLICATE_KEY"])
    finally:
        handle.close()

    handle, writer = csv_writer(output / "INCOMPLETE_KEYS.csv",
        ["SOURCE", "CSV_RECORD_NUMBER", *KEYS, "MISSING_KEY_FIELDS"])
    try:
        for src, rn, subj, visit, visitn, order in db.execute(
            "SELECT src,rn,subj,visit,visitn,visit_order FROM records WHERE kh IS NULL ORDER BY src,rn"):
            values = (subj, visit, visitn, order)
            writer.writerow(["OLD" if src == 1 else "NEW", rn, *values,
                             "; ".join(k for k, v in zip(KEYS, values) if not v)])
    finally:
        handle.close()

    # Only unambiguous 1-to-1 matches can support a defensible cell comparison.
    # Old nonempty values missing in new and changed values are separate categories.
    handle, writer = csv_writer(output / "VALUE_DIFFERENCES.csv",
        ["USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER", "COLUMN",
         "OLD_VALUE", "NEW_VALUE", "STATUS", "OLD_CSV_RECORD", "NEW_CSV_RECORD"])
    per_column = Counter()
    try:
        sql = """
            SELECT p.subj,p.visit,p.visitn,p.visit_order,c.col,c.val,
                   n.val,p.old_rn,p.new_rn
            FROM pairs p JOIN cells c ON c.src=1 AND c.rn=p.old_rn
            LEFT JOIN cells n ON n.src=2 AND n.rn=p.new_rn AND n.col=c.col
            WHERE n.val IS NULL OR n.val<>c.val
        """
        for subj, visit, visitn, order, col, oldval, newval, oldrn, newrn in db.execute(sql):
            status = "MISSING_IN_NEW" if newval is None else "DIFFERENT_VALUE"
            summary[status.lower()] += 1
            per_column[(col, status)] += 1
            writer.writerow([subj, visit, visitn, order, col, oldval, newval or "", status, oldrn, newrn])
    finally:
        handle.close()

    summary["old_cells_in_unambiguous_matched_rows"] = scalar(db, """
        SELECT COUNT(*) FROM pairs p JOIN cells c ON c.src=1 AND c.rn=p.old_rn
    """)
    summary["same_value_cells_in_matched_rows"] = (
        summary["old_cells_in_unambiguous_matched_rows"]
        - summary["missing_in_new"] - summary["different_value"]
    )
    with (output / "VARIABLE_DIFFERENCES_SUMMARY.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["COLUMN", "MISSING_IN_NEW", "DIFFERENT_VALUE"])
        for col in sorted({x[0] for x in per_column}):
            w.writerow([col, per_column[(col, "MISSING_IN_NEW")], per_column[(col, "DIFFERENT_VALUE")]])

    # Report all old rows not uniquely paired: no unsafe assumption of coverage.
    handle, writer = csv_writer(output / "UNMATCHED_OLD_ROWS.csv",
        ["OLD_CSV_RECORD", *KEYS, "REASON"])
    try:
        sql = """
          SELECT r.rn,r.subj,r.visit,r.visitn,r.visit_order,r.kh,g.old_n,g.new_n
          FROM records r LEFT JOIN groups g ON g.kh=r.kh
          LEFT JOIN pairs p ON p.old_rn=r.rn
          WHERE r.src=1 AND p.old_rn IS NULL ORDER BY r.rn
        """
        for rn, subj, visit, visitn, order, kh, on, nn in db.execute(sql):
            reason = ("INCOMPLETE_KEY" if kh is None else
                      "KEY_ABSENT_IN_NEW" if nn == 0 else
                      "AMBIGUOUS_DUPLICATE_KEY")
            writer.writerow([rn, subj, visit, visitn, order, reason])
    finally:
        handle.close()

    with (output / "SUMMARY.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["METRIC", "VALUE"])
        for key, val in summary.items():
            w.writerow([key, val])
        for key in KEYS:
            w.writerow([f"old_missing_{key}", old_missing[key]])
            w.writerow([f"new_missing_{key}", new_missing[key]])

    return summary


def main():
    start = time.time()
    old = INPUT_FOLDER / OLD_FILE
    new = INPUT_FOLDER / NEW_FILE
    for path in (old, new):
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix.lower() != ".csv":
            raise ValueError(f"Only CSV files are supported: {path}")
    if old.resolve() == new.resolve():
        raise ValueError("OLD_FILE and NEW_FILE must be different files")
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(OUTPUT_FOLDER).free < MIN_FREE_GB * (1024**3):
        raise RuntimeError(f"At least {MIN_FREE_GB} GiB free disk space required")
    dbpath = OUTPUT_FOLDER / "ard_comparison_working.sqlite"
    if dbpath.exists():
        raise FileExistsError(f"Working database already exists: {dbpath}. Remove only if no run is active.")
    db = sqlite3.connect(dbpath)
    success = False
    try:
        setup(db)
        print("[1/3] Importing OLD CSV...", flush=True)
        old_stats, old_missing = import_file(db, old, 1)
        print("[2/3] Importing NEW CSV...", flush=True)
        new_stats, new_missing = import_file(db, new, 2)
        print("[3/3] Comparing and exporting reports...", flush=True)
        summary = compare(db, OUTPUT_FOLDER, old_stats, new_stats, old_missing, new_missing)
        print("\nRESULTS")
        for metric, val in summary.items():
            print(f"  {metric}: {val:,}")
        print("\nINTERPRETATION:")
        if (summary["old_columns_absent_in_new"] == 0
            and summary["old_incomplete_key_rows"] == 0
            and summary["old_complete_key_rows_not_uniquely_matched"] == 0
            and summary["missing_in_new"] == 0
            and summary["different_value"] == 0):
            print("  All OLD records were uniquely matched and all OLD populated values agree with NEW.")
        else:
            print("  Full OLD-data coverage by NEW is NOT established. Review the CSV reports.")
            print("  Incomplete/duplicate keys are NOT automatically treated as missing data.")
        print(f"Reports: {OUTPUT_FOLDER}")
        print(f"Elapsed: {(time.time()-start)/60:.1f} min")
        success = True
    finally:
        db.close()
        if success and not KEEP_SQLITE:
            dbpath.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
