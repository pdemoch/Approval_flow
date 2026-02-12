import streamlit as st
# Incluído o import da view de usuários
from src.views import login, transportador, validacao, faturamento, gestao, usuarios 

st.set_page_config(page_title="Sistema Logístico - Linea", layout="wide")

# Inicialização de Sessão
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# Sidebar e Logout
if st.session_state.user:
    with st.sidebar:
        st.image("https://www.lineaalimentos.com.br/wp-content/themes/linea/assets/images/logo.png", width=150)
        st.divider()
        # Tratamento simples para evitar erro caso st.session_state.email não exista
        email_display = st.session_state.get('email', 'Usuário').split('@')[0].capitalize()
        st.write(f"👤 **{email_display}**")
        st.caption(f"🔑 Perfil: {st.session_state.role.capitalize()}")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.email = None
            st.rerun()

# Roteamento de Telas
if not st.session_state.user:
    login.render()
else:
    role = st.session_state.role

    if role == "transportador":
        transportador.render()

    elif role == "validacao":
        validacao.render()

    elif role == "faturamento":
        faturamento.render()

    elif role == "gestao":
        gestao.render()

    elif role == "admin":
        # Adicionada a aba "Configurações de Usuários"
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Gestão/BI", 
            "⚖️ Validação", 
            "💰 Faturamento", 
            "🚚 Visão Transportador",
            "👥 Usuários"
        ])
        
        with tab1:
            gestao.render()
        with tab2:
            validacao.render()
        with tab3:
            faturamento.render()
        with tab4:
            transportador.render()
        with tab5:
            usuarios.render() # <-- Renderiza a gestão de permissões

    else:
        st.error(f"Perfil '{role}' não reconhecido. Contrate o suporte.")