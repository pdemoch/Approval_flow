import streamlit as st
from src.database import db, supabase # Importe os dois no topo
from src.views import login, transportador, validacao, faturamento, gestao, usuarios 

st.set_page_config(page_title="Sistema Logístico - Linea", layout="wide")

# --- INICIALIZAÇÃO DE SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "email" not in st.session_state: # Garanta que o email comece como None
    st.session_state.email = None

# --- SIDEBAR E LOGOUT ---
if st.session_state.user:
    with st.sidebar:
        st.image("https://www.lineaalimentos.com.br/wp-content/themes/linea/assets/images/logo.png", width=150)
        st.divider()
        
        # Uso do .get para evitar quebra caso o email seja None
        email_val = st.session_state.get('email')
        email_display = email_val.split('@')[0].capitalize() if email_val else "Usuário"
        
        st.write(f"👤 **{email_display}**")
        st.caption(f"🔑 Perfil: {str(st.session_state.role).capitalize()}")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.email = None
            st.rerun()

# --- ROTEAMENTO DE TELAS ---
if not st.session_state.user:
    login.render()
else:
    # 1. SEGURANÇA: Só consulta o banco se tivermos o email na sessão
    if st.session_state.email:
        try:
            # Busca status e flag de troca de senha
            res = db.table("profiles").select("status", "troca_senha_obrigatoria").eq("email", st.session_state.email).single().execute()
            
            if res.data:
                status = res.data.get("status")
                troca_obrigatoria = res.data.get("troca_senha_obrigatoria")

                # A. Bloqueio de Aprovação
                if status != "ativo":
                    st.error("🚫 **Acesso Suspenso ou Pendente.**")
                    st.info("Seu cadastro foi recebido e aguarda aprovação do administrador da Linea.")
                    if st.button("Voltar ao Login"):
                        st.session_state.user = None
                        st.rerun()
                    st.stop()

                # B. Bloqueio de Troca de Senha
                if troca_obrigatoria:
                    st.warning("🔒 **Segurança: Primeiro Acesso**")
                    st.subheader("Defina sua nova senha:")
                    
                    with st.form("form_troca_senha"):
                        nova_senha = st.text_input("Nova Senha", type="password")
                        confirma = st.text_input("Confirme a Nova Senha", type="password")
                        
                        if st.form_submit_button("Atualizar e Acessar"):
                            if nova_senha == confirma and len(nova_senha) >= 6:
                                try:
                                    # Atualiza senha no Auth e flag no Profile
                                    supabase.auth.update_user({"password": nova_senha})
                                    db.table("profiles").update({"troca_senha_obrigatoria": False}).eq("email", st.session_state.email).execute()
                                    
                                    st.success("✅ Senha atualizada!")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao atualizar: {e}")
                            else:
                                st.error("Senhas divergentes ou menores que 6 caracteres.")
                    st.stop() 

        except Exception as e:
            st.error(f"Erro de permissão: {e}")
            st.stop()

    # 2. ROTEAMENTO NORMAL
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
        t1, t2, t3, t4, t5 = st.tabs(["📊 BI", "⚖️ Validação", "💰 Finanças", "🚚 Transportador", "👥 Usuários"])
        with t1: gestao.render()
        with t2: validacao.render()
        with t3: faturamento.render()
        with t4: transportador.render()
        with t5: usuarios.render()
    else:
        st.error(f"Perfil '{role}' não reconhecido.")