#!/usr/bin/env python3
"""Generate ARGES-ready video coverage from a read-only Thea.View inventory CSV.

Requires: pandas, openpyxl (no artifact_tool or API access).
Example:
  python 02_generate_video_reports.py --input video_inventory_output_power/all_video_inventory.csv --output-dir video_reports_output_power
  python 02_generate_video_reports.py --input video_inventory_output_anthem/all_video_inventory_corrected.csv --output-dir video_reports_output_anthem --scheduled-visits "Screening,Week 12,Week 28"
"""
import argparse
import re
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

QUASAR_SCHEDULED = ['Screening', 'I-12', 'I-24', 'M-44', 'M-92', 'M-140', 'M-188', 'M-236']
REQUIRED = {'study', 'data_type', 'site', 'patient_id', 'visit', 'filename',
            'video_class', 'examination_date', 'anatomical_region'}
METRICS = ['unique_patients_at_visit', 'file_items', 'technical_recordings_est',
           'cumulative_unique_patients', 'complete_longitudinal_patients']


def norm_name(value):
    value = re.sub(r'\.[^.]+$', '', str(value).strip(), flags=re.I)
    value = re.sub(r'(?i)(?:[._ -]+transcoded)+$', '', value)
    return re.sub(r'\s+', ' ', value).strip().casefold()


def excel(path, tabs):
    wb = Workbook()
    wb.remove(wb.active)
    for name, frame in tabs.items():
        ws = wb.create_sheet(name)
        ws.append(list(frame.columns))
        for row in frame.itertuples(index=False, name=None):
            ws.append([None if pd.isna(v) else v.item() if hasattr(v, 'item') else v for v in row])
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.fill = PatternFill('solid', fgColor='24344A')
            cell.font = Font(bold=True, color='FFFFFF')
            cell.alignment = Alignment(wrap_text=True, vertical='center')
        ws.row_dimensions[1].height = 36
        for i, col in enumerate(ws.columns, 1):
            vals = [str(c.value if c.value is not None else '') for c in col]
            width = min(58, max(15, max((len(v) for v in vals), default=15) + 2))
            ws.column_dimensions[get_column_letter(i)].width = width
    wb.save(path)


def main():
    ap = argparse.ArgumentParser(description='Generate QUASAR-style video coverage for any study')
    ap.add_argument('--input', default='video_inventory_output/all_video_inventory.csv')
    ap.add_argument('--output-dir', default='video_reports_output')
    ap.add_argument('--scheduled-visits', default=None,
                    help='Comma-separated scheduled visits in protocol order')
    args = ap.parse_args()
    src = Path(args.input)
    if not src.is_file():
        ap.error(f'Input not found: {src}')
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    missing = REQUIRED - set(df.columns)
    if missing:
        ap.error(f'Missing columns: {sorted(missing)}')
    if df.empty:
        ap.error('Empty inventory: cannot infer study from an empty CSV')
    df = df.copy()
    for col in REQUIRED:
        df[col] = df[col].str.strip()
    df['patient_key'] = df['site'] + '::' + df['patient_id']
    df['valid_patient'] = df['site'].ne('') & df['patient_id'].ne('')
    df['recording_name'] = df['filename'].map(norm_name)
    identity = ['study', 'data_type', 'site', 'patient_id', 'visit',
                'examination_date', 'anatomical_region', 'recording_name']
    priority = {'RAW_ORIGINAL': 0, 'RAW_UNCLASSIFIED': 1,
                'RAW_TRANSCODED': 2, 'PROCESSED': 0}
    df['priority'] = df['video_class'].map(priority).fillna(3)
    rep = df.sort_values('priority', kind='stable').drop_duplicates(identity)

    if args.scheduled_visits is not None:
        specified = [v.strip() for v in args.scheduled_visits.split(',') if v.strip()]
        if not specified or len(specified) != len(set(specified)):
            ap.error('--scheduled-visits must contain nonempty, unique visits')
    else:
        specified = None

    studies, visit_rows, qa = [], [], []
    definitions = pd.DataFrame([
        ('visit_type', 'SCHEDULED if included in supplied/QUASAR schedule; otherwise UNCLASSIFIED or UNSCHEDULED/UNMATCHED.'),
        ('unique_patients_at_visit', 'Distinct site + patient_id combinations with at least one video file at this visit.'),
        ('file_items', 'Video file items, including possible transcoded versions and duplicates.'),
        ('technical_recordings_est', 'Filename/metadata-based estimate; not clinically verified unique recordings.'),
        ('cumulative_unique_patients', 'Union of patients with videos across scheduled visits through this visit.'),
        ('complete_longitudinal_patients', 'Intersection of patients with videos at every scheduled visit through this visit.'),
        ('unscheduled visits', 'Included in overall totals but excluded from scheduled cumulative/longitudinal calculations.'),
        ('zero counts', 'A zero means no matching items in this inventory; verify extraction completeness and patient IDs.'),
        ('data_source', 'Read-only Thea.View Girder inventory; not a protocol compliance measure.')
    ], columns=['metric', 'interpretation'])

    for study, sg in df.groupby('study', sort=True):
        if specified is not None:
            scheduled = specified
        elif 'QUASAR' in study.upper():
            scheduled = QUASAR_SCHEDULED
        else:
            scheduled = []
            print(f'WARNING: {study}: scheduled visit order not supplied; cumulative and longitudinal counts left blank.')
        rec = {'study': study}
        for typ, tag in [('rawdata', 'raw'), ('processed', 'processed')]:
            part = sg.loc[sg['data_type'].eq(typ)]
            rec[f'total_{tag}_file_items'] = len(part)
            rec[f'total_{tag}_unique_patients'] = part.loc[part['valid_patient'], 'patient_key'].nunique()
            flags = part['needs_review'] if 'needs_review' in part.columns else pd.Series('', index=part.index)
            qa.append({'study': study, 'data_type': typ, 'file_items': len(part),
                       'estimated_technical_recordings': len(rep.loc[rep['study'].eq(study) & rep['data_type'].eq(typ)]),
                       'missing_patient_identifiers': int((~part['valid_patient']).sum()),
                       'source_flagged_review': int(flags.str.lower().isin(['true', '1', 'yes']).sum())})
        studies.append(rec)

        for typ in ('rawdata', 'processed'):
            part = sg.loc[sg['data_type'].eq(typ)]
            rpart = rep.loc[rep['study'].eq(study) & rep['data_type'].eq(typ)]
            visits = scheduled + sorted(set(part['visit']) - set(scheduled), key=str.casefold)
            seen, complete = set(), None
            for visit in visits:
                pf = part.loc[part['visit'].eq(visit)]
                pr = rpart.loc[rpart['visit'].eq(visit)]
                patients = set(pf.loc[pf['valid_patient'], 'patient_key'])
                if visit in scheduled:
                    seen |= patients
                    complete = patients if complete is None else complete & patients
                    cumulative, longitudinal = len(seen), len(complete)
                    visit_type = 'SCHEDULED'
                else:
                    cumulative, longitudinal = None, None
                    visit_type = 'UNCLASSIFIED' if not scheduled else 'UNSCHEDULED/UNMATCHED'
                visit_rows.append({
                    'study': study, 'visit': visit, 'visit_type': visit_type, 'data_type': typ,
                    'unique_patients_at_visit': len(patients), 'file_items': len(pf),
                    'technical_recordings_est': len(pr),
                    'cumulative_unique_patients': cumulative,
                    'complete_longitudinal_patients': longitudinal
                })

    summary = pd.DataFrame(studies)
    visits = pd.DataFrame(visit_rows, columns=['study', 'visit', 'visit_type', 'data_type'] + METRICS)
    qa_df = pd.DataFrame(qa)

    def prepare_sheet(data_type):
        part = visits.loc[visits['data_type'].eq(data_type),
                          ['study', 'visit', 'visit_type'] + METRICS].copy()
        return part.rename(columns={m: f'{data_type}_{m}' for m in METRICS}).reset_index(drop=True)

    raw = prepare_sheet('rawdata')
    processed = prepare_sheet('processed')
    summary.to_csv(out / 'video_study_summary.csv', index=False, encoding='utf-8-sig')
    visits.to_csv(out / 'video_visit_coverage.csv', index=False, encoding='utf-8-sig')
    qa_df.to_csv(out / 'video_quality_checks.csv', index=False, encoding='utf-8-sig')
    excel(out / 'video_study_summary.xlsx', {'study_summary': summary, 'definitions': definitions})
    excel(out / 'video_visit_coverage.xlsx',
          {'raw_videos': raw, 'processed_videos': processed, 'definitions': definitions})
    print('Generated:', out.resolve())
    print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
