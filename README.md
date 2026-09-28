# example1

import pandas as pd
import streamlit as st
from src.ui import show_table,download_row

def render(filtered,data):
    st.header('Data Availability'); st.markdown('<div class="section-note">Availability matrix across source data, SDTM/ADaM, ARD, annotations, clinical ground truth and feature vectors.</div>',unsafe_allow_html=True)
    df=filtered.get('02_DATA_AVAILABILITY',pd.DataFrame()); cols=[c for c in ['Videos','SDTM/ADaM (Med.ai)','SDTM/ADaM (Domino)','Analysis-Ready-Dataset (ARD)','Symptom Data','QS','ADQS','Feature Vectors'] if c in df.columns]; c1,c2,c3=st.columns(3); c1.metric('Studies',df['Study ID'].nunique() if 'Study ID' in df else 0)
    if cols:
        v=df[cols].astype(str).apply(lambda x:x.str.lower()); c2.metric('Available cells',int(v.eq('available').sum().sum())); c3.metric('Pending cells',int(v.eq('pending').sum().sum()))
    show_table(df,key='availability_table',link_cols=['Clinical GT Location']); download_row(df,'filtered_data_availability')
