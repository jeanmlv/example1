# example1

import pandas as pd
import streamlit as st
from src.ui import show_table,donut_from_status

def render(filtered,data):
    st.header('External Data'); st.markdown('<div class="section-note">External datasets, access status, licensing, provenance, and intended use.</div>',unsafe_allow_html=True); df=data.get('08_EXTERNAL_ANALYSIS',pd.DataFrame()).copy(); q=st.text_input('Search external datasets',placeholder='dataset, domain, modality, provider...')
    if q and not df.empty:
        mask=pd.Series(False,index=df.index)
        for c in df.columns: mask|=df[c].fillna('').astype(str).str.contains(q,case=False,regex=False)
        df=df[mask]
    c1,c2,c3=st.columns(3); c1.metric('External datasets',len(df)); c2.metric('Available',df['Access Status'].astype(str).str.lower().eq('available').sum() if 'Access Status' in df else 0); c3.metric('Modalities',df['Data Modality'].nunique() if 'Data Modality' in df else 0); donut_from_status(df,'Access Status','External data access'); show_table(df,key='external_table',max_rows=16,link_cols=['License / Terms Link'])

