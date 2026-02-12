import streamlit as st
from src.database import db, supabase  # Importamos ambos: cliente de auth e db

def render():
    st.image("https://www.lineaalimentos.com.br/wp-content/themes/linea/assets/images/logo.png", width=180)
    
    tab_login, tab_req, tab_reset = st.tabs(["🔑 Acessar", "📝 Solicitar Cadastro", "🔄 Recuperar Senha"])

    # --- ABA 1: LOGIN REAL ---
    with tab_login:
        with st.form("login_form"):
            email_input = st.text_input("E-mail").lower().strip()
            senha_input = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Entrar", use_container_width=True):
                if email_input and senha_input:
                    try:
                        # 1. Tenta autenticar no Supabase Auth
                        auth_res = supabase.auth.sign_in_with_password({
                            "email": email_input,
                            "password": senha_input
                        })
                        
                        if auth_res.user:
                            # 2. Busca o perfil na nossa tabela customizada
                            profile_res = db.table("profiles").select("*").eq("email", email_input).single().execute()
                            
                            if profile_res.data:
                                # 3. Salva na sessão e redireciona
                                st.session_state.user = auth_res.user
                                st.session_state.email = email_input
                                st.session_state.role = profile_res.data.get("role")
                                st.success("Login realizado com sucesso!")
                                st.rerun()
                            else:
                                st.error("Perfil não encontrado na base de dados.")
                    except Exception as e:
                        st.error("E-mail ou senha incorretos. Verifique seus dados.")
                else:
                    st.warning("Preencha todos os campos.")

    # --- ABA 2: SOLICITAÇÃO DE CADASTRO ---
    with tab_req:
        st.subheader("Nova Solicitação de Acesso")
        st.caption("Seu acesso passará por aprovação da administração.")
        
        with st.form("request_form", clear_on_submit=True):
            nome = st.text_input("Nome de Contato")
            email_reg = st.text_input("E-mail para Login").lower().strip()
            role_desejada = st.selectbox("Perfil Desejado", ["transportador", "faturamento", "validacao"])
            
            st.divider()
            st.write("📩 **E-mails para Notificação**")
            c1, c2 = st.columns(2)
            with c1: e_sec1 = st.text_input("E-mail Adicional 1")
            with c2: e_sec2 = st.text_input("E-mail Adicional 2")
            
            st.divider()
            senha_reg = st.text_input("Crie uma senha inicial", type="password", help="Mínimo 6 caracteres")
            
            if st.form_submit_button("Enviar Solicitação", use_container_width=True):
                if email_reg and nome and len(senha_reg) >= 6:
                    try:
                        # 1. Cria o usuário no Auth (sem confirmar e-mail se configurado no Supabase)
                        supabase.auth.sign_up({
                            "email": email_reg,
                            "password": senha_reg
                        })
                        
                        # 2. Insere na tabela de profiles como PENDENTE
                        db.table("profiles").insert({
                            "email": email_reg,
                            "nome_contato": nome,
                            "role": role_desejada,
                            "email_secundario_1": e_sec1,
                            "email_secundario_2": e_sec2,
                            "status": "pendente",
                            "troca_senha_obrigatoria": True
                        }).execute()
                        
                        st.success("✅ Solicitação enviada! Aguarde a aprovação do Admin.")
                    except Exception as e:
                        st.error(f"Erro ao processar cadastro: {e}")
                else:
                    st.warning("Preencha Nome, E-mail e Senha corretamente.")

    # --- ABA 3: RECUPERAÇÃO DE SENHA ---
    with tab_reset:
        st.subheader("Esqueceu sua senha?")
        st.write("Informe seu e-mail para receber um link de redefinição.")
        email_reset = st.text_input("E-mail cadastrado", key="reset_email")
        
        if st.button("Enviar Link de Recuperação", use_container_width=True):
            if email_reset:
                try:
                    supabase.auth.reset_password_for_email(email_reset)
                    st.success("Link enviado! Verifique sua caixa de entrada.")
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.warning("Informe o e-mail.")