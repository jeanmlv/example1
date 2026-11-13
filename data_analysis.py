import re
import pandas as pd
import plotly.express as px
import streamlit as st
from src.ui import show_table

SHEET = '07_DATA_ANALYSIS'
RED = '#E2231A'
STATUS_COLORS = {'Complete': '#16B878', 'Failed': '#E2231A', 'Running': '#4299E1', 'Pending': '#F59E0B', 'Not specified': '#808899'}
MISSING = {'', '-', '—', 'nan', 'none', 'n/a', 'na', 'nat', '<na>'}


def clean(value):
    if pd.isna(value):
        return ''
    value = str(value).strip()
    return '' if value.lower() in MISSING else value


def prepare(df, studies):
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.startswith('Unnamed:')]
    df = df.dropna(how='all')
    for col in df.columns:
        df[col] = df[col].map(clean)
    if 'Running ID' in df:
        df = df[df['Running ID'].ne('')].copy()
    for col in ['Running ID', 'Study ID', 'Study Name', 'Status', 'Deployment Platform', 'Analysis Owner', 'Analysis Date']:
        if col not in df:
            df[col] = ''
    aliases = {'completed': 'Complete', 'complete': 'Complete', 'failed': 'Failed', 'failure': 'Failed', 'running': 'Running', 'in progress': 'Running', 'pending': 'Pending'}
    df['Status'] = df['Status'].map(lambda x: aliases.get(x.lower(), x or 'Not specified'))
    for col in ['Deployment Platform', 'Analysis Owner']:
        df[col] = df[col].replace('', 'Not specified')
    if {'Study ID', 'Study Name'}.issubset(studies.columns):
        names = studies[['Study ID', 'Study Name']].dropna().copy()
        names['Study ID'] = names['Study ID'].map(clean)
        names['Study Name'] = names['Study Name'].map(clean)
        lookup = names.drop_duplicates('Study ID').set_index('Study ID')['Study Name']
        df['Study Name'] = df['Study ID'].map(lookup).replace('', pd.NA).fillna(df['Study Name'])
    df['_date'] = pd.to_datetime(df['Analysis Date'], errors='coerce')
    df['Analysis Date'] = df['_date'].dt.strftime('%Y-%m-%d').fillna(df['Analysis Date'])
    return df.reset_index(drop=True)


def explorer(df):
    st.subheader('Analysis Explorer')
    query = st.text_input('Search analyses', placeholder='Study, analysis, model, running ID...', key='analysis_search').strip()
    a, b, c = st.columns(3)
    for container, col, label in [(a, 'Deployment Platform', 'Platform'), (b, 'Status', 'Status'), (c, 'Analysis Owner', 'Owner')]:
        options = sorted(df[col].unique().tolist())
        selected = container.multiselect(label, options, key='analysis_filter_' + col)
        if selected:
            df = df[df[col].isin(selected)]
    if query:
        mask = df.drop(columns=['_date']).apply(lambda s: s.str.contains(query, case=False, regex=False, na=False)).any(axis=1)
        df = df[mask]
    return df


def chart(fig, height=300):
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=height, margin=dict(l=10,r=20,t=15,b=10), legend_title_text='')
    st.plotly_chart(fig, use_container_width=True)


def summary(df):
    n = len(df)
    complete = int(df['Status'].eq('Complete').sum())
    failed = int(df['Status'].eq('Failed').sum())
    cols = st.columns(3)
    cols[0].metric('Analysis Runs', n)
    cols[1].metric('Studies', df['Study ID'].replace('', pd.NA).nunique())
    cols[2].metric('Platforms', df['Deployment Platform'].replace('Not specified', pd.NA).nunique())
    cols = st.columns(3)
    cols[0].metric('Completed', complete)
    cols[1].metric('Failed', failed)
    cols[2].metric('Completion Rate', f'{100*complete/n:.1f}%', help='Complete analysis records divided by all filtered analysis records; not model accuracy or video processing success.')
    st.subheader('Execution Status')
    counts = df['Status'].value_counts().rename_axis('Status').reset_index(name='Runs')
    counts['Share'] = counts['Runs'] / n * 100
    counts['Group'] = 'All runs'
    counts['Label'] = counts.apply(lambda r: f"{r['Runs']} ({r['Share']:.1f}%)", axis=1)
    fig = px.bar(counts, x='Share', y='Group', color='Status', orientation='h', text='Label', color_discrete_map=STATUS_COLORS, hover_data={'Runs':True,'Share':':.1f','Group':False,'Label':False})
    fig.update_layout(barmode='stack', xaxis=dict(range=[0,100], visible=False), yaxis=dict(visible=False), legend=dict(orientation='h', y=-0.15))
    chart(fig, 150)


def visualizations(df):
    left, right = st.columns(2)
    with left:
        st.subheader('Runs by Study')
        known = df[df['Study ID'].ne('')]
        counts = known.groupby('Study ID').agg(Study=('Study Name','first'), Runs=('Study ID','size')).reset_index()
        counts['Study'] = counts['Study'].where(counts['Study'].ne(''), counts['Study ID'])
        counts = counts.sort_values('Runs')
        if not counts.empty:
            fig = px.bar(counts, x='Runs', y='Study', orientation='h', text='Runs', hover_data=['Study ID'], color_discrete_sequence=[RED])
            fig.update_layout(xaxis=dict(dtick=1), yaxis_title=None)
            chart(fig, max(300, 35*len(counts)+70))
        else:
            st.info('No identified studies.')
        if len(known) != len(df):
            st.caption(f'{len(df)-len(known)} runs without a Study ID excluded.')
    with right:
        st.subheader('Execution Platforms')
        counts = df['Deployment Platform'].value_counts().rename_axis('Platform').reset_index(name='Runs')
        fig = px.bar(counts, x='Runs', y='Platform', orientation='h', text='Runs', color_discrete_sequence=['#F46B62'])
        fig.update_layout(yaxis_title=None, xaxis=dict(dtick=1), yaxis=dict(autorange='reversed'))
        chart(fig)
    st.subheader('Analysis Activity')
    period = st.radio('Group by', ['Day','Week','Month'], horizontal=True, key='analysis_period')
    dated = df.dropna(subset=['_date']).copy()
    if dated.empty:
        st.info('No valid analysis dates available.')
        return
    dated['Period'] = dated['_date'].dt.to_period({'Day':'D','Week':'W-SUN','Month':'M'}[period]).dt.start_time
    counts = dated.groupby(['Period','Status']).size().reset_index(name='Runs')
    fig = px.bar(counts, x='Period', y='Runs', color='Status', color_discrete_map=STATUS_COLORS)
    fig.update_layout(barmode='stack', xaxis_title=None, yaxis=dict(dtick=1))
    chart(fig)
    st.caption(f'{len(dated)} of {len(df)} runs have valid analysis dates. Weeks start Monday.')


def registry(df):
    st.subheader('Analysis Registry')
    groups = {
        'All runs': ['Running ID','Study Name','Analysis Name','Deployment Platform','Analysis Date','Status'],
        'Execution details': ['Running ID','Analysis ID','Study ID','Study Name','Input Dataset','Videos','Dataset Location','Analysis Owner','Analysis Date'],
        'Models & Code': ['Running ID','Study Name','Dataset / Model Version','DSA Model Card','Code Repository','Code Path / Script','Code Version / Commit','SAP Reference','SAP Version','SAP Location'],
        'Results & Reports': ['Running ID','Study Name','Status','Reports Location','Notes'],
    }
    for i, (tab, fields) in enumerate(zip(st.tabs(list(groups)), groups.values())):
        with tab:
            cols = [c for c in fields if c in df]
            # Keep mixed S3 paths and multi-link text intact, not as a single URL.
            show_table(df[cols], key=f'analysis_registry_{i}')
    st.subheader('Analysis Details')
    rows = df.reset_index(drop=True)
    idx = st.selectbox('Select analysis run', list(rows.index), format_func=lambda i: f"{rows.at[i,'Running ID']} — {rows.at[i,'Study Name']} — {rows.at[i,'Analysis Name'] if 'Analysis Name' in rows else ''}", key='analysis_detail')
    row = rows.loc[idx]
    st.markdown('**' + (row.get('Analysis Name') or 'Analysis run') + '**')
    a,b,c = st.columns(3)
    a.metric('Status', row['Status'])
    b.metric('Study', row['Study Name'] or '—')
    c.metric('Date', row['Analysis Date'] or '—')
    for heading, fields in groups.items():
        if heading == 'All runs':
            continue
        with st.expander(heading, expanded=heading=='Results & Reports'):
            for col in fields:
                if col in row and clean(row[col]):
                    st.markdown(f'**{col}**')
                    value = str(row[col])
                    st.text(value)
                    for url in dict.fromkeys(re.findall(r'https?://[^\s|<>]+', value)):
                        st.markdown(f'[Open reference]({url})')
    extra = [c for c in df.columns if c != '_date' and not any(c in fields for fields in groups.values()) and clean(row[c])]
    if extra:
        with st.expander('Additional metadata'):
            for col in extra:
                st.write(col, row[col])


def render(filtered, data):
    st.header('Data Analysis')
    st.markdown('<div class="section-note">Analysis execution, model versions, reproducibility and results across the ARGES portfolio.</div>', unsafe_allow_html=True)
    df = prepare(filtered.get(SHEET, pd.DataFrame()), data.get('01_STUDIES', pd.DataFrame()))
    if df.empty:
        st.info('No analysis records match the current study filters.')
        return
    total = len(df)
    df = explorer(df)
    st.caption(f'{len(df)} of {total} analysis records in the selected study scope.')
    if df.empty:
        st.info('No analyses match the current filters.')
        return
    summary(df)
    st.divider()
    visualizations(df)
    st.divider()
    registry(df)
