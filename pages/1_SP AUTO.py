import streamlit as st
from modules import module_one
import pandas as pd
import io
from streamlit_extras.colored_header import colored_header

buffer = io.BytesIO()

st.set_page_config(
    page_title="Module 1: SP AUTO",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

colored_header(
    label='SP AUTO',
    color_name= 'yellow-80'
)

if 'access' not in st.session_state:
    st.session_state['access'] = False
if 'module_name' not in st.session_state:
    st.session_state['module_name'] = None
if 'email' not in st.session_state:
    st.session_state['email'] = None
if 'date' not in st.session_state:
    st.session_state['date'] = None

st.session_state['module_name'] = 'SP AUTO'

def module_1():
    output_dataframe = pd.DataFrame()

    with st.form('form-1', border=True):
        data_file = st.file_uploader('Upload your excel data', type=['xlsx'])
        with st.expander('Look at what your Input data looks like'):
            if data_file is not None:
                input_df = pd.read_excel(data_file).dropna(how='all')
                st.table(input_df.head())
                output_dataframe = module_one.proccess_df(input_df)
        st.form_submit_button('Start Processing')

    if not output_dataframe.empty:
        with st.expander('Look at what your Output data looks like'):
            st.table(output_dataframe.head())
                
        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        output_dataframe.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.close()
        file_name = st.session_state['email'].split('@')[0]
        st.download_button(
            label="Download Output",
            data=buffer,
            file_name=f"Output_{st.session_state['module_name']}_{file_name}_{st.session_state['date']}.xlsx",
            mime="application/vnd.ms-excel"
        )

if st.session_state['access']:
    module_1()
else:
    st.warning('Go to Homepage to login before you can access any module')