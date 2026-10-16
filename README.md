# example1

import pandas as pd
import plotly.express as px
import streamlit as st
from src.ui import show_table,download_row

def render(filtered,data):
    st.header('Analysis-Ready Data (ARD)'); st.markdown('<div class="section-note">ARD inventory, variable-of-interest mapping coverage, and gap status by study.</div>',unsafe_allow_html=True); df=filtered.get('06_ARD',pd.DataFrame()); c1,c2,c3,c4=st.columns(4); c1.metric('ARD records',len(df)); mapped=pd.to_numeric(df.get('Mapped'),errors='coerce').sum() if 'Mapped' in df else 0; missing=pd.to_numeric(df.get('Missing'),errors='coerce').sum() if 'Missing' in df else 0; c2.metric('Mapped VOI',f'{mapped:,.0f}'); c3.metric('Missing VOI',f'{missing:,.0f}'); avg=pd.to_numeric(df.get('Coverage %'),errors='coerce').mean() if 'Coverage %' in df else float('nan'); # Mean coverage: consider only studies with >= 1% coverage
coverage = pd.to_numeric( a.get("Coverage %", pd.Series(dtype=float)), errors="coerce") valid_coverage = coverage[coverage >= 1] avg = valid_coverage.mean() c4.metric( "Mean coverage", f"{avg:.0f}%" if pd.notna(avg) else "—")
    if not df.empty and {'Study Name','Coverage %'}.issubset(df):
        cols=['Study Name','Coverage %']+(['Coverage Level'] if 'Coverage Level' in df else []); x=df[cols].copy(); x['Coverage %']=pd.to_numeric(x['Coverage %'],errors='coerce'); fig=px.bar(x.dropna(subset=['Coverage %']).sort_values('Coverage %'),x='Coverage %',y='Study Name',orientation='h',color='Coverage Level' if 'Coverage Level' in x else None,text_auto='.0%',color_discrete_map={'High':'#12B76A','Medium':'#F79009','Low':'#D92D20'}); fig.update_xaxes(tickformat='.0%',range=[0,1]); fig.update_layout(height=max(330,28*len(x)),margin=dict(l=5,r=5,t=15,b=10),yaxis_title='',legend_title_text=''); st.plotly_chart(fig,use_container_width=True)
    show_table(df,key='ard_table',link_cols=['Location']); download_row(df,'filtered_ard')

