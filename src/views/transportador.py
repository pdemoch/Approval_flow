import streamlit as st
import pandas as pd
from src.database import db
import uuid

# --- FUNÇÕES DE APOIO ---
def upload_arquivos(files):
    urls = []
    bucket = "comprovantes"
    for arquivo in files:
        try:
            file_ext = arquivo.name.split(".")[-1]
            file_name = f"{uuid.uuid4()}.{file_ext}"
            db.storage.from_(bucket).upload(
                path=file_name,
                file=arquivo.getvalue(),
                file_options={"content-type": arquivo.type}
            )
            public_url = db.storage.from_(bucket).get_public_url(file_name)
            urls.append(public_url)
        except Exception as e:
            st.error(f"Erro no upload: {e}")
            return None
    return urls

# --- MODAL DE DETALHES E EDIÇÃO ---
@st.dialog("📋 Detalhes da Solicitação")
def modal_detalhes(item):
    st.markdown(f"### Solicitação NF: {item['numero_nf']}")
    st.write(f"**Status Atual:** `{item['status']}`")
    
    pode_editar = item['status'] == 'Pendente Documentos'
    
    if item.get('observacao'):
        st.error(f"**Motivo da Pendência:** {item['observacao']}")

    with st.form("form_edicao_detalhe"):
        c1, c2 = st.columns(2)
        novo_cliente = c1.text_input("Cliente", value=item['cliente'], disabled=not pode_editar)
        novo_valor = c2.number_input("Valor", value=float(item['valor']), disabled=not pode_editar)
        
        st.write("**Arquivos Anexados:**")
        cols_docs = st.columns(len(item['comprovante_url']) if item['comprovante_url'] else 1)
        for idx, url in enumerate(item['comprovante_url']):
            cols_docs[idx % len(cols_docs)].link_button(f"📄 Doc {idx+1}", url, use_container_width=True)
            
        if pode_editar:
            st.info("💡 Corrija os dados acima ou anexe novos arquivos para reenviar.")
            novos_up = st.file_uploader("Adicionar novos comprovantes", accept_multiple_files=True)
            
            if st.form_submit_button("✅ Salvar e Reenviar"):
                payload = {
                    "cliente": novo_cliente,
                    "valor": novo_valor,
                    "status": "Aberto",
                    "observacao": None
                }
                if novos_up:
                    urls_novas = upload_arquivos(novos_up)
                    payload["comprovante_url"] = item['comprovante_url'] + urls_novas
                
                db.table("solicitacoes").update(payload).eq("id", item['id']).execute()
                st.success("Solicitação atualizada!")
                st.rerun()
        else:
            if st.form_submit_button("Fechar"):
                st.rerun()

# --- VIEW PRINCIPAL ---
def render():
    # --- CSS LINEA ALIMENTOS ---
    st.markdown("""
        <style>
        /* Título e textos */
        .main h1 { color: #002D58; } /* Azul Marinho Linea */
        
        /* Estilização dos Botões de Filtro */
        div.stButton > button {
            height: 80px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        /* Cores específicas por Botão (Identidade Linea) */
        button[key="f_todos"] { background-color: #002D58 !important; color: white !important; border: none; }
        button[key="f_pendente"] { background-color: #E30613 !important; color: white !important; border: none; } /* Vermelho Alerta */
        button[key="f_analise"] { background-color: #009FE3 !important; color: white !important; border: none; }  /* Azul Claro Linea */
        button[key="f_faturado"] { background-color: #28A745 !important; color: white !important; border: none; } /* Verde Sucesso */
        
        button:hover { transform: scale(1.02); opacity: 0.9; }
        
        /* Ajuste da Tabela */
        [data-testid="stMetricValue"] { color: #002D58; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚚 Painel do Transportador")
    st.caption(f"Acesso: {st.session_state['email']} | **Portal de Custos Logísticos**")

    if "filtro_status" not in st.session_state:
        st.session_state.filtro_status = "Todos"

    # Busca dados
    try:
        response = db.table("solicitacoes").select("*").eq("user_id", st.session_state["user"].id).order("id", desc=True).execute()
        df = pd.DataFrame(response.data)
    except:
        st.error("Falha ao carregar dados.")
        return

    # --- DASHBOARD DE FILTROS ---
    if not df.empty:
        st.subheader("Filtrar por Status")
        cols = st.columns(4)
        
        # Botões que agem como Filtros Clicáveis
        if cols[0].button(f"🔵 TODOS\n{len(df)}", key="f_todos"): st.session_state.filtro_status = "Todos"
        
        pen = len(df[df['status'] == 'Pendente Documentos'])
        if cols[1].button(f"🔴 PENDENTES\n{pen}", key="f_pendente"): st.session_state.filtro_status = "Pendente Documentos"
        
        ana = len(df[df['status'] == 'Aberto'])
        if cols[2].button(f"🟡 ANÁLISE\n{ana}", key="f_analise"): st.session_state.filtro_status = "Aberto"
        
        fat = len(df[df['faturado'] == True])
        if cols[3].button(f"🟢 FATURADOS\n{fat}", key="f_faturado"): st.session_state.filtro_status = "Finalizado"

    # --- ÁREA DE CORREÇÃO RÁPIDA ---
    pendencias_df = df[df['status'] == 'Pendente Documentos'] if not df.empty else pd.DataFrame()
    if not pendencias_df.empty:
        st.error(f"🛑 ATENÇÃO: Você possui {len(pendencias_df)} solicitações com erro. Clique na lista abaixo para corrigir.")

    # --- NOVA SOLICITAÇÃO ---
    with st.expander("➕ Registrar Novo Custo Logístico", expanded=False):
        with st.form("form_nova_linea", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nf = c1.text_input("Número da Nota Fiscal")
            cli = c2.text_input("Nome do Cliente")
            tipo = c1.selectbox("Tipo de Operação", ["Diaria", "Devolução", "Paletização", "Pernoite", "Ajudante"])
            val = c2.number_input("Valor Reembolso (R$)", min_value=0.0, step=0.01)
            up = st.file_uploader("Anexar Comprovantes (Múltiplos)", accept_multiple_files=True)
            
            if st.form_submit_button("Enviar para Validação", type="primary"):
                if nf and cli and up:
                    urls = upload_arquivos(up)
                    if urls:
                        payload = {
                            "user_id": st.session_state["user"].id,
                            "solicitante_email": st.session_state["email"],
                            "numero_nf": nf, "cliente": cli, "tipo_custo": tipo, "valor": val,
                            "comprovante_url": urls, "status": "Aberto"
                        }
                        db.table("solicitacoes").insert(payload).execute()
                        st.success("Solicitação enviada com sucesso!")
                        st.rerun()
                else:
                    st.warning("Preencha os campos obrigatórios e anexe os documentos.")

    # --- LISTA DE SOLICITAÇÕES ---
    st.divider()
    df_filtrado = df if st.session_state.filtro_status == "Todos" else df[df['status'] == st.session_state.filtro_status]
    
    st.subheader(f"Lista: {st.session_state.filtro_status}")
    
    if not df_filtrado.empty:
        # Interface de Seleção e Ação
        col_sel, col_btn = st.columns([3, 1])
        selecionado = col_sel.selectbox("Selecione uma linha para ver detalhes:", 
                                  df_filtrado.index, 
                                  format_func=lambda x: f"NF: {df_filtrado.loc[x, 'numero_nf']} | {df_filtrado.loc[x, 'cliente']} ({df_filtrado.loc[x, 'status']})")
        
        if col_btn.button("🔍 Ver Detalhes / Editar", use_container_width=True):
            modal_detalhes(df_filtrado.loc[selecionado].to_dict())

        st.dataframe(
            df_filtrado,
            column_config={
                "id": "ID", "user_id": None, "solicitante_email": None,
                "created_at": st.column_config.DatetimeColumn("Data Solicitação", format="D/M/Y HH:mm"),
                "numero_nf": "NF", "cliente": "Cliente",
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "status": "Status Atual",
                "comprovante_url": None,
                "observacao": "Observação"
            },
            hide_index=True, use_container_width=True
        )
    else:
        st.info("Nenhuma solicitação encontrada para este filtro.")