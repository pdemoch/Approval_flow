import streamlit as st
import pandas as pd
from src.database import db

def render():
    st.title("👥 Gestão de Usuários")
    st.caption("Administração de acessos e permissões da Linea Alimentos")

    # --- 1. FORMULÁRIO DE CADASTRO ---
    with st.expander("➕ Cadastrar Novo Perfil ou Atualizar Único"):
        with st.form("novo_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("E-mail do Usuário")
            with col2:
                role = st.selectbox("Perfil de Acesso", 
                                   ["transportador", "validacao", "faturamento", "gestao", "admin"])
            
            if st.form_submit_button("🚀 Salvar Perfil", use_container_width=True):
                if email:
                    try:
                        db.table("profiles").upsert({
                            "email": email.lower().strip(),
                            "role": role
                        }, on_conflict="email").execute()
                        st.success(f"✅ Perfil de {email} definido como {role}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {e}")
                else:
                    st.warning("⚠️ O e-mail é obrigatório.")

    st.divider()

    # --- 2. LISTA E EDIÇÃO EM LOTE ---
    st.subheader("📋 Lista de Usuários e Permissões")
    
    try:
        res = db.table("profiles").select("*").order("email").execute()
        if res.data:
            df_original = pd.DataFrame(res.data)

            # Filtro de Busca
            busca = st.text_input("🔍 Buscar por e-mail", placeholder="Digite parte do e-mail...")
            df_filtered = df_original[df_original['email'].str.contains(busca, case=False)] if busca else df_original

            # Editor de Dados
            # O st.data_editor retorna o dataframe com as edições feitas pelo usuário
            df_editado = st.data_editor(
                df_filtered,
                column_config={
                    "id": None, 
                    "email": st.column_config.TextColumn("E-mail (Login)", width="large"),
                    "role": st.column_config.SelectboxColumn(
                        "Cargo / Permissão",
                        options=["transportador", "validacao", "faturamento", "gestao", "admin"],
                        width="medium"
                    ),
                    "created_at": st.column_config.DatetimeColumn("Criado em", format="DD/MM/YY HH:mm")
                },
                use_container_width=True,
                disabled=["email", "created_at"], # Protege o e-mail, edita apenas a role
                key="editor_usuarios"
            )

            # Lógica para Salvar Alterações em Lote
            # Comparamos o df_editado com o original para saber o que mudou
            if st.button("💾 Salvar Alterações em Lote", type="primary"):
                changes = df_editado[df_editado['role'] != df_filtered['role']]
                
                if not changes.empty:
                    with st.spinner("Atualizando permissões..."):
                        for _, row in changes.iterrows():
                            db.table("profiles").update({"role": row['role']}).eq("email", row['email']).execute()
                    st.success(f"✅ {len(changes)} perfil(is) atualizado(s) com sucesso!")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração detectada nos cargos.")

        else:
            st.info("Nenhum perfil encontrado no banco de dados.")

    except Exception as e:
        st.error(f"❌ Erro ao carregar usuários: {e}")