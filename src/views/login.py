import streamlit as st
from src.database import db, supabase

# --- FUNÇÕES DE SUPORTE (Lógica isolada) ---

def handle_login(email, password):
    """Gerencia a autenticação e busca de perfil."""
    try:
        auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if auth_res.user:
            profile = db.table("profiles").select("*").eq("email", email).single().execute()
            if profile.data:
                status = profile.data.get("status")
                if status == "pendente":
                    st.warning("⏳ Cadastro em análise pela administração.")
                    return
                if status == "suspenso":
                    st.error("🚫 Acesso suspenso.")
                    return
                
                # Sucesso: Preenche sessão
                st.session_state.user = auth_res.user
                st.session_state.email = email
                st.session_state.role = profile.data.get("role")
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Perfil não encontrado na base de dados.")
    except Exception as e:
        st.error(f"E-mail ou senha incorretos.")

def handle_request(nome, email, role, e1, e2, senha):
    """Gerencia a criação de conta e perfil com proteção contra erros de duplicidade."""
    try:
        # 1. SignUp no Auth (Ignora se já existir para permitir recuperar o 'Profile')
        try:
            supabase.auth.sign_up({"email": email, "password": senha})
        except Exception as e:
            if "already registered" not in str(e): raise e

        # 2. Upsert no Profiles (Solução definitiva para o erro de 'E-mail já existe')
        db.table("profiles").upsert({
            "email": email,
            "nome_contato": nome,
            "role": role,
            "email_secundario_1": e1 if e1 else None,
            "email_secundario_2": e2 if e2 else None,
            "status": "pendente",
            "troca_senha_obrigatoria": True
        }, on_conflict="email").execute()

        st.success(f"✅ Solicitação para '{role.capitalize()}' enviada!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao processar: {str(e)}")

# --- INTERFACE PRINCIPAL ---

def render():
    st.image("https://d3p2amk7tvag7f.cloudfront.net/brands/cf5d5446a2f529654d1f3e3e8ff0f6ca24729485.png", width=180)
    
    tabs = st.tabs(["🔑 Acessar", "📝 Solicitar Cadastro", "🔄 Recuperar Senha"])

    # ABA: LOGIN
    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("E-mail").lower().strip()
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if email and senha: handle_login(email, senha)
                else: st.warning("Informe credenciais válidas.")

    # ABA: SOLICITAÇÃO
    with tabs[1]:
        st.subheader("Nova Solicitação de Acesso")
        with st.form("request_form", clear_on_submit=True):
            nome = st.text_input("Nome de Contato")
            email_reg = st.text_input("E-mail para Login").lower().strip()
            role = st.selectbox("Perfil Desejado", ["transportador", "faturamento", "validacao", "gestao", "admin"])
            
            st.divider()
            c1, c2 = st.columns(2)
            e_sec1 = c1.text_input("E-mail Adicional 1")
            e_sec2 = c2.text_input("E-mail Adicional 2")
            
            st.divider()
            senha_reg = st.text_input("Senha inicial (mín. 6 caracteres)", type="password")
            
            if st.form_submit_button("Enviar Solicitação", use_container_width=True):
                if email_reg and nome and len(senha_reg) >= 6:
                    handle_request(nome, email_reg, role, e_sec1, e_sec2, senha_reg)
                else:
                    st.warning("Preencha os campos obrigatórios corretamente.")

    # ABA: RESET
    with tabs[2]:
        st.subheader("Recuperar Senha")
        email_reset = st.text_input("E-mail cadastrado", key="reset_email")
        if st.button("Enviar Link", use_container_width=True):
            if email_reset:
                try:
                    supabase.auth.reset_password_for_email(email_reset)
                    st.success("Link enviado! Verifique sua caixa de entrada.")
                except: st.error("Erro ao enviar link.")