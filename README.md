# example1

#!/usr/bin/env python3
"""Generate ARGES-ready video coverage in the QUASAR workbook layout.

Requires: pandas, openpyxl. No API calls; reads inventory CSV only.
For reliable cumulative/longitudinal metrics provide --scheduled-visits in protocol order.
"""
import argparse
import re
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

QUASAR_SCHEDULED = ['Screening','I-12','I-24','M-44','M-92','M-140','M-188','M-236']
REQUIRED = {'study','data_type','site','patient_id','visit','filename','video_class','examination_date','anatomical_region'}

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
        ws.row_dimensions[1].height = 35
        for i, col in enumerate(ws.columns, 1):
            vals = [str(c.value or '') for c in col]
            width = min(58, max(15, max((len(v) for v in vals), default=15) + 2))
            ws.column_dimensions[get_column_letter(i)].width = width
    wb.save(path)

def main():
    ap = argparse.ArgumentParser(description='Generate QUASAR-style visit coverage for any study')
    ap.add_argument('--input', default='video_inventory_output/all_video_inventory.csv')
    ap.add_argument('--output-dir', default='video_reports_output')
    ap.add_argument('--scheduled-visits', default=None, help='Comma-separated scheduled visits in protocol order (e.g. Screening,Week 8,Week 16)')
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
        ap.error('Empty inventory')
    df = df.copy()
    for col in REQUIRED:
        df[col] = df[col].str.strip()
    df['patient_key'] = df.site + '::' + df.patient_id
    df['valid_patient'] = df.site.ne('') & df.patient_id.ne('')
    df['recording_name'] = df.filename.map(norm_name)
    identity = ['study','data_type','site','patient_id','visit','examination_date','anatomical_region','recording_name']
    priority = {'RAW_ORIGINAL':0,'RAW_UNCLASSIFIED':1,'RAW_TRANSCODED':2,'PROCESSED':0}
    df['priority'] = df.video_class.map(priority).fillna(3)
    rep = df.sort_values('priority', kind='stable').drop_duplicates(identity)
    studies, visit_rows, qa = [], [], []
    definitions = pd.DataFrame([
        ('visit_type','Classification as scheduled or unscheduled. Requires a verified protocol schedule for non-QUASAR studies.'),
        ('unique_patients_at_visit','Distinct site + patient_id combinations with at least one video file at this visit.'),
        ('file_items','Number of video file items, including original/transcoded/other versions.'),
        ('technical_recordings_est','Metadata/filename-based estimate of distinct technical recordings, not clinically verified.'),
        ('cumulative_unique_patients','Distinct patients with video at any scheduled visit up to this visit (union).'),
        ('*Unscheduled visits','Excluded from scheduled cumulative and longitudinal calculations.'),
        ('complete_longitudinal_patients','Patients with videos at every scheduled visit through this visit (intersection).'),
        ('data_source','Read-only Thea.View Girder inventory; not a measure of protocol compliance.')
    ], columns=['metric','interpretation'])
    for study, sg in df.groupby('study', sort=True):
        if args.scheduled_visits is not None:
            scheduled = [v.strip() for v in args.scheduled_visits.split(',') if v.strip()]
            if not scheduled or len(scheduled) != len(set(scheduled)):
                ap.error('--scheduled-visits must contain nonempty, unique visits')
        elif 'QUASAR' in study.upper():
            scheduled = QUASAR_SCHEDULED
        else:
            scheduled = []
            print(f'WARNING: {study}: scheduled visit order not supplied; cumulative and longitudinal counts left blank.')
        rec = {'study': study}
        for typ, tag in [('rawdata','raw'),('processed','processed')]:
            part = sg[sg.data_type == typ]
            rec[f'total_{tag}_file_items'] = len(part)
            rec[f'total_{tag}_unique_patients'] = part.loc[part.valid_patient,'patient_key'].nunique()
            flags = part['needs_review'] if 'needs_review' in part else pd.Series('',index=part.index)
            qa.append({'study':study,'data_type':typ,'file_items':len(part),
                       'estimated_technical_recordings':len(rep[(rep.study==study)&(rep.data_type==typ)]),
                       'missing_patient_identifiers':int((~part.valid_patient).sum()),
                       'source_flagged_review':int(flags.str.lower().isin(['true','1','yes']).sum())})
        studies.append(rec)
        for typ, tag in [('rawdata','rawdata'),('processed','processed')]:
            part = sg[sg.data_type == typ]
            rpart = rep[(rep.study==study)&(rep.data_type==typ)]
            visits = scheduled + sorted(set(part.visit) - set(scheduled), key=str.casefold)
            seen, complete = set(), None
            for visit in visits:
                pf = part[part.visit == visit]
                pr = rpart[rpart.visit == visit]
                patients = set(pf.loc[pf.valid_patient,'patient_key'])
                if visit in scheduled:
                    seen |= patients
                    complete = patients if complete is None else complete & patients
                    cumulative, longitudinal = len(seen), len(complete)
                    visit_type = 'SCHEDULED'
                else:
                    cumulative, longitudinal = None, None
                    visit_type = 'UNCLASSIFIED' if not scheduled else 'UNSCHEDULED/UNMATCHED'
                visit_rows.append({'study':study,'visit':visit,'visit_type':visit_type,
                    f'{tag}_unique_patients_at_visit':len(patients),
                    f'{tag}_file_items':len(pf),
                    f'{tag}_technical_recordings_est':len(pr),
                    f'{tag}_cumulative_unique_patients':cumulative,
                    f'{"raw_data" if typ=="rawdata" else "processed"}_complete_longitudinal_patients':longitudinal,
                    '_data_type':typ})
    summary = pd.DataFrame(studies)
    visits = pd.DataFrame(visit_rows)

    metric_names = [
        'unique_patients_at_visit',
        'file_items',
        'technical_recordings_est',
        'cumulative_unique_patients',
        'complete_longitudinal_patients'
    ]

    def prepare_sheet(data_type):
        part = visits.loc[visits['data_type'] == data_type].copy()

    columns = ['study', 'visit', 'visit_type']

    prefix = 'rawdata' if data_type == 'rawdata' else 'processed'

    for metric in metric_names:
        source_col = f'{prefix}_{metric}'
        if source_col not in part.columns:
            part[source_col] = 0 if metric in metric_names[:3] else None
        columns.append(source_col)

    return part[columns].reset_index(drop=True)

raw = prepare_sheet('rawdata')
processed = prepare_sheet('processed')
    visits = pd.DataFrame(visit_rows)
    raw = visits[visits._data_type=='rawdata'].drop(columns='_data_type').reset_index(drop=True)
    processed = visits[visits._data_type=='processed'].drop(columns='_data_type').reset_index(drop=True)
    # Keep only columns matching the requested reference workbook for each sheet.
    # Preserve all generated columns without selecting nonexistent names.
    raw = raw.reset_index(drop=True)
    processed = processed.reset_index(drop=True)

    # Display available columns for validation.
    print("RAW columns:", raw.columns.tolist())
    print("PROCESSED columns:", processed.columns.tolist())
    processed = processed[['study','visit','visit_type','processed_unique_patients_at_visit','processed_file_items','processed_technical_recordings_est','processed_cumulative_unique_patients','processed_complete_longitudinal_patients']]
    summary.to_csv(out/'video_study_summary.csv',index=False,encoding='utf-8-sig')
    visits.to_csv(out/'video_visit_coverage.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(qa).to_csv(out/'video_quality_checks.csv',index=False,encoding='utf-8-sig')
    excel(out/'video_study_summary.xlsx', {'study_summary':summary,'definitions':definitions})
    excel(out/'video_visit_coverage.xlsx', {'raw_videos':raw,'processed_videos':processed,'definitions':definitions})
    print('Generated:',out.resolve())
    print(summary.to_string(index=False))

if __name__ == '__main__':
    main()
