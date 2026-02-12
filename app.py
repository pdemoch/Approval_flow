import streamlit as st
from src.database import db
from src.views import login, transportador, validacao, faturamento, gestao, usuarios 

st.set_page_config(page_title="Sistema Logístico - Linea", layout="wide")

# --- INICIALIZAÇÃO DE SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- SIDEBAR E LOGOUT ---
if st.session_state.user:
    with st.sidebar:
        st.image("https://www.lineaalimentos.com.br/wp-content/themes/linea/assets/images/logo.png", width=150)
        st.divider()
        email_display = st.session_state.get('email', 'Usuário').split('@')[0].capitalize()
        st.write(f"👤 **{email_display}**")
        st.caption(f"🔑 Perfil: {st.session_state.role.capitalize()}")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.email = None
            st.rerun()

# --- ROTEAMENTO DE TELAS ---
if not st.session_state.user:
    login.render()
else:
    # 1. BUSCA DADOS DE SEGURANÇA NO BANCO (Status e Troca de Senha)
    try:
        user_data = db.table("profiles").select("status", "troca_senha_obrigatoria").eq("email", st.session_state.email).single().execute()
        
        if user_data.data:
            status = user_data.data.get("status")
            troca_obrigatoria = user_data.data.get("troca_senha_obrigatoria")

            # A. Verifica se o usuário foi aprovado
            if status != "ativo":
                st.error("🚫 **Acesso Suspenso ou Pendente.** Seu cadastro ainda não foi aprovado pelo administrador.")
                if st.button("Voltar ao Login"):
                    st.session_state.user = None
                    st.rerun()
                st.stop()

            # B. Sequestro de Tela: Troca de Senha Obrigatória
            if troca_obrigatoria:
                st.warning("🔒 **Segurança: Troca de Senha Obrigatória**")
                st.info("Este é seu primeiro acesso ou sua senha foi resetada. Defina uma nova senha para continuar.")
                
                with st.form("form_troca_senha"):
                    nova_senha = st.text_input("Nova Senha", type="password")
                    confirma = st.text_input("Confirme a Nova Senha", type="password")
                    
                    if st.form_submit_button("Atualizar Senha e Entrar"):
                        if nova_senha == confirma and len(nova_senha) >= 6:
                            # Atualiza no Banco
                            db.table("profiles").update({"troca_senha_obrigatoria": False}).eq("email", st.session_state.email).execute()
                            # DICA: Aqui você chamaria o supabase.auth.update_user se estivesse usando Auth real
                            st.success("Senha atualizada! Redirecionando...")
                            st.rerun()
                        else:
                            st.error("As senhas não coincidem ou são muito curtas (min. 6 caracteres).")
                st.stop() # Interrompe a renderização do resto do app

    except Exception as e:
        st.error(f"Erro ao verificar permissões: {e}")
        st.stop()

    # 2. ROTEAMENTO NORMAL (Só chega aqui se Status=Ativo e Troca=False)
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
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Gestão/BI", "⚖️ Validação", "💰 Faturamento", "🚚 Visão Transportador", "👥 Usuários"
        ])
        with tab1: gestao.render()
        with tab2: validacao.render()
        with tab3: faturamento.render()
        with tab4: transportador.render()
        with tab5: usuarios.render()

    else:
        st.error(f"Perfil '{role}' não reconhecido. Contrate o suporte.")