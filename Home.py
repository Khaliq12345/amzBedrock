import streamlit as st
from streamlit_extras.colored_header import colored_header
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import json
import requests
from time import sleep

rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

cred_json = {
  "type": st.secrets['TYPE'],
  "project_id": st.secrets['PROJECT_ID'],
  "private_key_id": st.secrets['PRIVATE_KEY_ID'],
  "private_key": st.secrets['PRIVATE_KEY'],
  "client_email": st.secrets['CLIENT_EMAIL'],
  "client_id": st.secrets['CLIENT_ID'],
  "auth_uri": st.secrets['AUTH_URI'],
  "token_uri": st.secrets['TOKEN_URI'],
  "auth_provider_x509_cert_url": st.secrets['AUTH_PROVIDER'],
  "client_x509_cert_url": st.secrets['CLIENT_URL'],
  "universe_domain": st.secrets['UNIVERSE_DOMAIN']
}

if 'access' not in st.session_state:
    st.session_state['access'] = False
if 'cred' not in st.session_state:
    st.session_state['cred'] = credentials.Certificate(cred_json)
if 'username' not in st.session_state:
    st.session_state['username'] = None

# admin = 'admin'
# pswd = 'admin12345'

def create_new_user(email, pswd, username):
    firebase_admin.initialize_app(st.session_state['cred'])
    auth.create_user(email=email, password=pswd, uid=username)
    
    try:
        user_ = auth.get_user(uid=username)
        return True
    except auth.UserNotFoundError:
        return False
    
def sign_in_with_username_and_password(username: str, password: str, return_secure_token: bool = True):
    payload = json.dumps({
        "email": f'{username}@gmail.com',
        "password": password,
        "returnSecureToken": return_secure_token
    })

    r = requests.post(rest_api_url,
                      params={"key": st.secrets['FIREBASE_WEB_API_KEY']},
                      data=payload)
    if r.status_code == 200:
      return True
    else:
      return False

def login_app():
    st.set_page_config(
        page_title="Login",
        page_icon="🔑",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    colored_header(
        label='🔑 Login',
        description= 'Welcome back! Please enter your username and password to log in.',
        color_name= 'blue-green-70'
    )
    
    st.session_state['username'] = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        with st.spinner('Signing in...'):
            signed_in = sign_in_with_username_and_password(st.session_state['username'], password)
        if signed_in:
            st.success("Logged in as {}".format(st.session_state['username']))
            st.session_state['access'] = True
            st.rerun()
        else:
            st.error("Invalid username or password")

def access_app():
    st.set_page_config(
        page_title="AMZBEDROCK",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    colored_header(
    label='📊 Data',
    description= 'Dev App',
    color_name= 'green-70'
    )
    
    st.success('Logged In!')

    st.write("""Use the sidebar to select the modules""")

    if st.button('Logout!'):
        st.session_state['access'] = False
        st.rerun()


if st.session_state['access']:
    access_app()
else:
    login_app()