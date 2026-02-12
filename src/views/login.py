import streamlit as st
from src.database import db

def render():
    st.image("https://www.lineaalimentos.com.br/wp-content/themes/linea/assets/images/logo.png", width=180)
    
    tab_login, tab_req = st.tabs(["🔑 Acessar Sistema", "📝 Solicitar Cadastro"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                # AQUI: Adicione sua lógica de st.session_state e autenticação
                st.info("Autenticação em processamento...")

    with tab_req:
        st.subheader("Nova Solicitação de Acesso")
        st.caption("Preencha os dados abaixo. Seu acesso passará por aprovação da Linea.")
        
        with st.form("request_form", clear_on_submit=True):
            nome = st.text_input("Nome de Contato (Pessoa Física)")
            email_login = st.text_input("E-mail para Login")
            
            col_roles = st.selectbox("Perfil Desejado", ["transportador", "faturamento", "validacao"])
            
            st.divider()
            st.write("📩 **E-mails para Notificação (Cópias)**")
            c1, c2 = st.columns(2)
            with c1:
                e_sec1 = st.text_input("E-mail Adicional 1")
            with c2:
                e_sec2 = st.text_input("E-mail Adicional 2")
            
            st.divider()
            senha_prov = st.text_input("Crie uma senha inicial", type="password", help="Mínimo 6 caracteres")
            
            if st.form_submit_button("Enviar Solicitação"):
                if email_login and nome and len(senha_prov) >= 6:
                    try:
                        # Criamos o perfil com status 'pendente'
                        db.table("profiles").insert({
                            "email": email_login.lower().strip(),
                            "nome_contato": nome,
                            "role": col_roles,
                            "email_secundario_1": e_sec1,
                            "email_secundario_2": e_sec2,
                            "status": "pendente",
                            "troca_senha_obrigatoria": True
                        }).execute()
                        
                        st.success("✅ Solicitação enviada com sucesso! Você receberá um e-mail quando o Admin aprovar.")
                    except Exception as e:
                        st.error(f"Erro ao solicitar: {e}")
                else:
                    st.warning("⚠️ Preencha Nome, E-mail e Senha (mín. 6 caracteres).")