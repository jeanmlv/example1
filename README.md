# example1

import pandas as pd
import streamlit as st
from src.ui import show_table,donut_from_status

def render(filtered,data):
    st.header('Data Analysis'); st.markdown('<div class="section-note">Analysis registry linking ARD inputs, SAP references, code versions, owners, and outputs.</div>',unsafe_allow_html=True); df=filtered.get('07_DATA_ANALYSIS',pd.DataFrame()); c1,c2,c3=st.columns(3); c1.metric('Analyses',len(df)); c2.metric('Studies',df['Study ID'].nunique() if 'Study ID' in df else 0); c3.metric('Owners',df['Analysis Owner'].nunique() if 'Analysis Owner' in df else 0); donut_from_status(df,'Status','Analysis status'); show_table(df,key='analysis_table',link_cols=['Dataset Location','SAP Location','Reports Location'])
