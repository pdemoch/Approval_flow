import streamlit as st
from src.views import login, transportador, validacao, faturamento

st.set_page_config(page_title="Sistema Logístico", layout="wide")

# Inicialização de Sessão
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# Sidebar e Logout
if st.session_state.user:
    with st.sidebar:
        st.write(f"👤 {st.session_state.email}")
        st.caption(f"Perfil: {st.session_state.role}")
        if st.button("Sair"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()

# Roteamento
if not st.session_state.user:
    login.render()
else:
    role = st.session_state.role
    if role == "transportador":
        transportador.render()
    elif role == "validacao" or role == "admin":
        validacao.render()
    elif role == "faturamento":
        faturamento.render()
    elif role == "admin":
        st.write("Visão Admin Global (Adicionar tabs aqui se quiser)")
        # Admin pode ver tudo, então poderia ter tabs para cada view
    else:
        st.error(f"Perfil {role} não configurado.")