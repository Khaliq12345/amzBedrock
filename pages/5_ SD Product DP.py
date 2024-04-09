import streamlit as st
from modules import module_five
import pandas as pd
import io
from streamlit_extras.colored_header import colored_header

buffer = io.BytesIO()

st.set_page_config(
    page_title="Module 5 -  SD Product DP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

colored_header(
    label='SD Product DP',
    color_name= 'red-70'
)

if 'access' not in st.session_state:
    st.session_state['access'] = False
if 'module_name' not in st.session_state:
    st.session_state['module_name'] = None
if 'email' not in st.session_state:
    st.session_state['email'] = None
if 'date' not in st.session_state:
    st.session_state['date'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

st.session_state['module_name'] = 'SD Product DP'

def show_input(data_file):
    with st.expander('Look at what your Input data looks like'):
        if data_file is not None:
            input_df = pd.read_excel(data_file).dropna(how='all')
            st.table(input_df.head())

def processing_input_file(data_file):
    output_dataframe = pd.DataFrame()
    if data_file is not None:
        input_df = pd.read_excel(data_file).dropna(how='all')
        try:
            output_dataframe = module_five.proccess_df(input_df)
        except Exception as e:
            st.error('Error parsing the input file. Kindly try again or contact the support')
            st.info(e)
    return output_dataframe

def module_5():
    with st.container(border=True):
        output_dataframe = pd.DataFrame()
        data_file = st.file_uploader('Upload your excel data', type=['xlsx'])
        col1, col2 = st.columns(2)
        show_input_button = col1.button('Show preview of the input data')
        if show_input_button:
            show_input(data_file)
        form_button = col2.button('Start Processing')
        if form_button:
            output_dataframe = processing_input_file(data_file)

    if not output_dataframe.empty:
        with st.expander('Look at what your Output data looks like'):
            st.table(output_dataframe.head())
                
        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        output_dataframe.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.close()
        file_name = st.session_state['username']
        st.download_button(
            label="Download Output",
            data=buffer,
            file_name=f"Output_{st.session_state['module_name']}_{file_name}_{st.session_state['date']}.xlsx",
            mime="application/vnd.ms-excel"
        )

if st.session_state['access']:
    module_5()
else:
    st.warning('Go to Homepage to login before you can access any module')