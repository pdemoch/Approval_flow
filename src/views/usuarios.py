import streamlit as st
import pandas as pd
from src.database import db

def render():
    st.title("👥 Gestão de Acessos e Permissões")
    
    # Criamos abas para separar quem já está ativo de quem está aguardando
    tab_ativos, tab_pendentes = st.tabs(["✅ Usuários Ativos", "⏳ Solicitações Pendentes"])

    # --- ABA 2: SOLICITAÇÕES PENDENTES ---
    with tab_pendentes:
        try:
            # Busca perfis com status pendente
            res_p = db.table("profiles").select("*").eq("status", "pendente").execute()
            
            if res_p.data:
                df_p = pd.DataFrame(res_p.data)
                st.warning(f"Existem {len(df_p)} solicitações aguardando sua .")
                
                for _, row in df_p.iterrows():
                    with st.container(border=True):
                        col_info, col_btn = st.columns([3, 1])
                        with col_info:
                            st.write(f"**E-mail:** {row['email']}")
                            st.write(f"**Nome:** {row.get('nome_contato', 'N/A')} | **Perfil Desejado:** `{row['role']}`")
                            st.caption(f"Secundários: {row.get('email_secundario_1')} / {row.get('email_secundario_2')}")
                        
                        with col_btn:
                            # Aprova o usuário mudando o status para ativo
                            if st.button("Aprovar ✅", key=f"app_{row['email']}", use_container_width=True):
                                db.table("profiles").update({"status": "ativo"}).eq("email", row['email']).execute()
                                st.success(f"Acesso liberado para {row['email']}")
                                st.rerun()
                            
                            # Recusa removendo o registro da tabela profiles
                            if st.button("Recusar ❌", key=f"rej_{row['email']}", use_container_width=True):
                                db.table("profiles").delete().eq("email", row['email']).execute()
                                st.rerun()
            else:
                st.info("Nenhuma solicitação pendente no momento.")
        except Exception as e:
            st.error(f"Erro ao carregar pendentes: {e}")

    # --- ABA 1: USUÁRIOS ATIVOS ---
    with tab_ativos:
        try:
            # Buscamos todos que não estão pendentes
            res = db.table("profiles").select("*").neq("status", "pendente").order("email").execute()
            
            if res.data:
                df_original = pd.DataFrame(res.data)
                
                busca = st.text_input("🔍 Buscar usuário ativo", placeholder="Digite o e-mail...")
                df_filtered = df_original[df_original['email'].str.contains(busca, case=False)] if busca else df_original

                # Editor de dados interativo
                df_editado = st.data_editor(
                    df_filtered,
                    column_config={
                        "id": None, # Esconde o ID técnico
                        "email": st.column_config.TextColumn("E-mail", width="large"),
                        "role": st.column_config.SelectboxColumn(
                            "Cargo", options=["transportador", "validacao", "faturamento", "gestao", "admin"]
                        ),
                        "status": st.column_config.SelectboxColumn("Status", options=["ativo", "suspenso"]),
                        "nome_contato": "Nome de Contato",
                        "troca_senha_obrigatoria": "Reset Senha?"
                    },
                    use_container_width=True,
                    disabled=["email", "id"], # Impede alterar o e-mail (chave primária lógica)
                    key="editor_ativos"
                )

                # --- LÓGICA DE SALVAMENTO EM LOTE ---
                if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                    with st.spinner("Sincronizando com o banco de dados..."):
                        try:
                            for index, row in df_editado.iterrows():
                                db.table("profiles").update({
                                    "role": row['role'],
                                    "status": row['status'],
                                    "nome_contato": row.get('nome_contato'),
                                    "troca_senha_obrigatoria": row.get('troca_senha_obrigatoria')
                                }).eq("email", row['email']).execute()
                            
                            st.success("✅ Todas as alterações foram salvas com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
            else:
                st.info("Nenhum usuário ativo encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar ativos: {e}")