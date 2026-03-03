import streamlit as st
from src.database import db, supabase

# --- FUNÇÃO DE LOGIN (RESTAURADA) ---
def handle_login(email, senha):
    try:
        # 1. Tenta autenticar no Supabase Auth
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        
        # 2. Busca os dados do perfil na tabela profiles
        profile = db.table("profiles").select("*").eq("email", email).single().execute()
        
        if not profile.data:
            st.error("Sua conta não possui um perfil configurado. Contate o suporte.")
            return

        user_data = profile.data

        # 3. VERIFICAÇÃO DE STATUS: Só deixa entrar se estiver ATIVO
        if user_data['status'] == 'pendente':
            st.warning("⏳ Sua conta ainda está aguardando aprovação do administrador.")
            return
        elif user_data['status'] == 'suspenso':
            st.error("🚫 Este acesso foi suspenso. Entre em contato com a gestão.")
            return

        # 4. SUCESSO: Salva na sessão e recarrega o app
        st.session_state["authenticated"] = True
        st.session_state["user"] = res.user
        st.session_state["email"] = email
        st.session_state["role"] = user_data['role']
        
        st.toast(f"Bem-vindo, {user_data.get('nome_contato', 'Usuário')}!", icon="👋")
        st.rerun()

    except Exception as e:
        # Erro genérico para não dar dicas a invasores
        st.error("❌ E-mail ou senha incorretos.")

# --- FUNÇÃO DE SOLICITAÇÃO ---
def handle_request(nome, email, role, e1, e2, senha, nome_empresa=None):
    try:
        check_user = db.table("profiles").select("email").eq("email", email).execute()
        if check_user.data:
            st.error("⚠️ Este e-mail já está cadastrado ou aguardando aprovação.")
            return

        supabase.auth.sign_up({"email": email, "password": senha})
        
        db.table("profiles").insert({
            "email": email,
            "nome_contato": nome,
            "role": role,
            "nome_transportador": nome_empresa,
            "email_secundario_1": e1 if e1 else None,
            "email_secundario_2": e2 if e2 else None,
            "status": "pendente",
            "troca_senha_obrigatoria": True
        }).execute()

        st.success("✅ Solicitação enviada! O administrador revisará seu acesso.")
        st.balloons()
    except Exception as e:
        if "unique_email" in str(e) or "already exists" in str(e).lower():
            st.error("🚫 Erro: Este e-mail já possui uma conta vinculada.")
        else:
            st.error(f"Erro inesperado: {str(e)}")

# --- VIEW PRINCIPAL ---
def render():
    st.image("https://d3p2amk7tvag7f.cloudfront.net/brands/cf5d5446a2f529654d1f3e3e8ff0f6ca24729485.png", width=180)
    
    tabs = st.tabs(["🔑 Acessar", "📝 Solicitar Cadastro", "🔄 Recuperar"])

    # ABA: LOGIN
    with tabs[0]:
        with st.form("login_form"):
            email_login = st.text_input("E-mail").lower().strip()
            senha_login = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Entrar", use_container_width=True):
                if email_login and senha_login:
                    handle_login(email_login, senha_login)
                else:
                    st.warning("Informe e-mail e senha.")

    # ABA: SOLICITAÇÃO
    with tabs[1]:
        st.subheader("Nova Solicitação de Acesso")
        
        role = st.selectbox(
            "Perfil Desejado", 
            ["transportador", "faturamento", "validacao", "gestao", "admin"]
        )

        with st.form("request_form_principal", clear_on_submit=True):
            nome = st.text_input("Nome de Contato")
            email_reg = st.text_input("E-mail para Login").lower().strip()
            
            nome_empresa = None
            if role == "transportador":
                nome_empresa = st.text_input("Nome da Empresa Transportadora *")
            
            st.divider()
            c1, c2 = st.columns(2)
            e_sec1 = c1.text_input("E-mail Adicional 1")
            e_sec2 = c2.text_input("E-mail Adicional 2")
            
            st.divider()
            senha_reg = st.text_input("Senha inicial (mín. 6 caracteres)", type="password")
            
            enviar = st.form_submit_button("Enviar Solicitação", type="primary", use_container_width=True)
            
            if enviar:
                if role == "transportador" and not nome_empresa:
                    st.error("Por favor, informe o nome da empresa transportadora.")
                elif email_reg and nome and len(senha_reg) >= 6:
                    handle_request(nome, email_reg, role, e_sec1, e_sec2, senha_reg, nome_empresa)
                else:
                    st.warning("Preencha todos os campos obrigatórios.")