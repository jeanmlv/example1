# example1

############# processing

import pandas as pd
import plotly.express as px
import streamlit as st
from src.ui import show_table

def render(filtered,data):
    st.header('Processing'); st.markdown('<div class="section-note">Pipeline readiness from preprocessing and feature extraction through CMES inference and modeling.</div>',unsafe_allow_html=True); df=filtered.get('04_PROCESSING',pd.DataFrame()); stages=[c for c in ['Preprocessing','Feature Extraction','CMES Inference','Modeling'] if c in df.columns]
    if stages and not df.empty:
        long=df.melt(id_vars=[c for c in ['Study ID','Study Name'] if c in df],value_vars=stages,var_name='Stage',value_name='Status'); long['Status']=long['Status'].fillna('Not specified'); x=long.groupby(['Stage','Status'],as_index=False).size().rename(columns={'size':'Studies'}); fig=px.bar(x,x='Stage',y='Studies',color='Status',barmode='stack',color_discrete_map={'Complete':'#12B76A','Pending':'#F79009','Not Started':'#D92D20','Not specified':'#D0D5DD'}); fig.update_layout(height=360,margin=dict(l=5,r=5,t=15,b=10),legend_title_text=''); st.plotly_chart(fig,use_container_width=True)
    show_table(df,key='processing_table')

########### data splits

import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import JNJ_RED
from src.ui import show_table

def render(filtered,data):
    st.header('Data Splits'); st.markdown('<div class="section-note">Study-level split definitions with subject/video-level detail where available.</div>',unsafe_allow_html=True); s=filtered.get('05_DATA_SPLITS',pd.DataFrame()); d=filtered.get('05A_DATA_SPLIT_DETAILS',pd.DataFrame()); c1,c2,c3,c4=st.columns(4); c1.metric('Split records',len(s)); c2.metric('Detail records',len(d)); c3.metric('Subjects',d['Subject ID'].nunique() if 'Subject ID' in d else 0); c4.metric('Videos / bags',d['Bag ID'].nunique() if 'Bag ID' in d else 0)
    if not s.empty and 'Split Type' in s:
        x=s['Split Type'].fillna('Not specified').value_counts().reset_index(); x.columns=['Split Type','Records']; fig=px.bar(x,x='Split Type',y='Records',text='Records',color_discrete_sequence=[JNJ_RED]); fig.update_layout(height=300,margin=dict(l=5,r=5,t=10,b=10),showlegend=False); st.plotly_chart(fig,use_container_width=True)
    t1,t2=st.tabs(['Split definitions','Split details'])
    with t1: show_table(s,key='split_table')
    with t2: show_table(d,key='split_details_table')
