import streamlit as st
from src.database import db, supabase

# --- FUNÇÃO DE ENVIO ATUALIZADA ---
def handle_request(nome, email, role, e1, e2, senha, nome_empresa=None):
    try:
        # 1. VERIFICAÇÃO PRÉVIA: O e-mail já existe no nosso banco?
        check_user = db.table("profiles").select("email").eq("email", email).execute()
        
        if check_user.data:
            st.error("⚠️ Este e-mail já está cadastrado ou aguardando aprovação.")
            return # Interrompe a função aqui

        # 2. SE NÃO EXISTE, tenta criar no Auth
        auth_res = supabase.auth.sign_up({"email": email, "password": senha})
        
        # 3. SE O AUTH DEU CERTO (ou se o usuário já existe no auth mas não no profiles)
        # Usamos INSERT em vez de UPSERT para garantir a unicidade
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
        # Tratamento para erro de duplicidade que venha direto do banco (segunda trava)
        if "unique_email" in str(e) or "already exists" in str(e).lower():
            st.error("🚫 Erro: Este e-mail já possui uma conta vinculada.")
        else:
            st.error(f"Erro inesperado: {str(e)}")

def render():
    st.image("https://d3p2amk7tvag7f.cloudfront.net/brands/cf5d5446a2f529654d1f3e3e8ff0f6ca24729485.png", width=180)
    
    tabs = st.tabs(["🔑 Acessar", "📝 Solicitar Cadastro", "🔄 Recuperar"])

    # ABA: LOGIN (Igual à anterior)
    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("E-mail").lower().strip()
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                # ... lógica de login (handle_login) ...
                pass

    # ABA: SOLICITAÇÃO (A MÁGICA ACONTECE AQUI)
    with tabs[1]:
        st.subheader("Nova Solicitação de Acesso")
        
        # 1. Seleção de Perfil FORA do Form para ser reativa
        role = st.selectbox(
            "Perfil Desejado", 
            ["transportador", "faturamento", "validacao", "gestao", "admin"],
            help="Selecione seu cargo para abrir os campos específicos."
        )

        # 2. Início do Formulário
        with st.form("request_form_principal", clear_on_submit=True):
            nome = st.text_input("Nome de Contato")
            email_reg = st.text_input("E-mail para Login").lower().strip()
            
            # Campo condicional que aparece se for transportador
            nome_empresa = None
            if role == "transportador":
                nome_empresa = st.text_input("Nome da Empresa Transportadora *")
            
            st.divider()
            c1, c2 = st.columns(2)
            e_sec1 = c1.text_input("E-mail Adicional 1")
            e_sec2 = c2.text_input("E-mail Adicional 2")
            
            st.divider()
            senha_reg = st.text_input("Senha inicial (mín. 6 caracteres)", type="password")
            
            # Botão de Envio
            enviar = st.form_submit_button("Enviar Solicitação", type="primary", use_container_width=True)
            
            if enviar:
                # Validação extra para transportadores
                if role == "transportador" and not nome_empresa:
                    st.error("Por favor, informe o nome da empresa transportadora.")
                elif email_reg and nome and len(senha_reg) >= 6:
                    handle_request(nome, email_reg, role, e_sec1, e_sec2, senha_reg, nome_empresa)
                else:
                    st.warning("Preencha todos os campos obrigatórios.")