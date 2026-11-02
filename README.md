# example1

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
