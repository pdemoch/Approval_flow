import streamlit as st
from src.database import db, supabase
from src.views import login, transportador, validacao, faturamento, gestao, usuarios 

st.set_page_config(page_title="Sistema Logístico - Linea", layout="wide")

# --- INICIALIZAÇÃO DE SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "email" not in st.session_state: 
    st.session_state.email = None

# --- SIDEBAR E LOGOUT ---
if st.session_state.user:
    with st.sidebar:
        st.image("https://d3p2amk7tvag7f.cloudfront.net/brands/cf5d5446a2f529654d1f3e3e8ff0f6ca24729485.png", width=150)
        st.divider()
        
        email_val = st.session_state.get('email')
        email_display = email_val.split('@')[0].capitalize() if email_val else "Usuário"
        
        st.write(f"👤 **{email_display}**")
        st.caption(f"🔑 Perfil: {str(st.session_state.role).capitalize()}")
        
        if st.button("🚪 Sair", use_container_width=True):
            # Limpeza completa para evitar cache de sessão
            for key in list(st.session_state.keys()):
                st.session_state[key] = None
            supabase.auth.sign_out() # Encerra sessão no servidor também
            st.rerun()

# --- ROTEAMENTO DE TELAS ---
if not st.session_state.user:
    login.render()
else:
    # 1. SEGURANÇA E VALIDAÇÃO DE STATUS
    if st.session_state.email:
        try:
            # Consulta as flags direto no banco para garantir tempo real
            res = db.table("profiles").select("status", "troca_senha_obrigatoria").eq("email", st.session_state.email).single().execute()
            
            if res.data:
                status = res.data.get("status")
                troca_obrigatoria = res.data.get("troca_senha_obrigatoria")

                # A. Bloqueio de Aprovação (Tratando Ativo vs Suspenso/Pendente)
                if status != "ativo":
                    st.error("🚫 **Acesso Restrito.**")
                    if status == "suspenso":
                        st.warning("Sua conta foi suspensa temporariamente. Entre em contato com o administrador.")
                    else:
                        st.info("Seu cadastro aguarda aprovação da administração.")
                    
                    if st.button("Voltar ao Login"):
                        st.session_state.user = None
                        st.rerun()
                    st.stop()

                # B. Fluxo de Troca de Senha Obrigatória
                if troca_obrigatoria:
                    st.warning("🔒 **Segurança: Primeiro Acesso**")
                    st.subheader("Defina sua nova senha:")
                    
                    with st.form("form_troca_senha"):
                        nova_senha = st.text_input("Nova Senha", type="password")
                        confirma = st.text_input("Confirme a Nova Senha", type="password")
                        
                        if st.form_submit_button("Atualizar e Acessar"):
                            if nova_senha == confirma and len(nova_senha) >= 6:
                                try:
                                    # 1. Atualiza no Auth (Serviço de Autenticação)
                                    supabase.auth.update_user({"password": nova_senha})
                                    # 2. Desativa a flag no Profiles (Seu Banco)
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
            # Caso o perfil tenha sido deletado mas o usuário ainda esteja logado no Auth
            st.error(f"Erro de perfil: Usuário não encontrado na base de dados.")
            if st.button("Fazer novo cadastro"):
                st.session_state.user = None
                st.rerun()
            st.stop()

    # 2. ROTEAMENTO POR PERFIL (ROLES)
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
        # Abas para visão total do Administrador
        t_bi, t_val, t_fin, t_trans, t_usr = st.tabs(["📊 BI", "⚖️ Validação", "💰 Finanças", "🚚 Transportador", "👥 Usuários"])
        with t_bi: gestao.render()
        with t_val: validacao.render()
        with t_fin: faturamento.render()
        with t_trans: transportador.render()
        with t_usr: usuarios.render()
    else:
        st.error(f"Perfil '{role}' não reconhecido pelo sistema.")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()