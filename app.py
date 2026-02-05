import streamlit as st
from auth.login import login
from auth.permissions import get_user_profile

st.set_page_config(page_title="Portal de Aprovação", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

user = st.session_state["user"]
profile = get_user_profile(user.id)

st.sidebar.title("Menu")

if profile["role"] == "transportador":
    st.title("🚚 Painel do Transportador")

elif profile["role"] == "torre":
    st.title("🛂 Painel Torre de Controle")

elif profile["role"] == "admin":
    st.title("🛠️ Painel Administrador")
