import streamlit as st
from modules import module_three
import pandas as pd
import io
from streamlit_extras.colored_header import colored_header

buffer = io.BytesIO()

st.set_page_config(
    page_title="Module 3 - SP ASIN PT",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

colored_header(
    label='SP ASIN PT',
    color_name= 'red-70'
)

if 'access' not in st.session_state:
    st.session_state['access'] = False
if 'module_name' not in st.session_state:
    st.session_state['module_name'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'date' not in st.session_state:
    st.session_state['date'] = None

st.session_state['module_name'] = 'SP ASIN PT'

def module_3():
    output_dataframe = pd.DataFrame()

    with st.form('form-1', border=True):
        data_file = st.file_uploader('Upload your excel data', type=['xlsx'])
        with st.expander('Look at what your Input data looks like'):
            if data_file is not None:
                input_df = pd.read_excel(data_file).dropna(how='all')
                st.table(input_df.head())
                output_dataframe = module_three.proccess_df(input_df)
        st.form_submit_button('Start Processing')

    if not output_dataframe.empty:
        with st.expander('Look at what your Output data looks like'):
            st.table(output_dataframe.head())
                
        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        output_dataframe.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.close()
        st.download_button(
            label="Download Output",
            data=buffer,
            file_name=f"Output_{st.session_state['module_name']}_{st.session_state['username']}_{st.session_state['date']}.xlsx",
            mime="application/vnd.ms-excel"
        )

if st.session_state['access']:
    module_3()
else:
    st.warning('Go to Homepage to login before you can access any module')