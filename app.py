import streamlit as st
from src.views import login, painel_transportador, painel_validacao, painel_faturamento

# Configuração da Página
st.set_page_config(page_title="Logística Workflow", layout="wide")

# Inicialização de Sessão
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# Lógica de Roteamento
if not st.session_state.user:
    login.render() # Tela de Login
else:
    # Menu Lateral
    with st.sidebar:
        st.write(f"Usuário: {st.session_state.user.email}")
        st.write(f"Perfil: {st.session_state.role}")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

    # Direcionamento por Perfil
    role = st.session_state.role
    
    if role == "transportador":
        painel_transportador.render()
    elif role == "validacao":
        painel_validacao.render()
    elif role == "faturamento":
        painel_faturamento.render()
    elif role == "admin":
        st.write("Painel Admin aqui")