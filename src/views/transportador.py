import streamlit as st
import pandas as pd
from src.database import db
from datetime import datetime
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

# --- MODAL DE DETALHES E EDIÇÃO (ESPELHO DO SEU FORMULÁRIO) ---
@st.dialog("📋 Detalhes e Edição da Solicitação")
def modal_detalhes(item):
    st.markdown(f"### NF: {item['numero_nf']}")
    
    pode_editar = item['status'] == 'Pendente Documentos'
    
    if item.get('observacao'):
        st.error(f"**Motivo da Pendência:** {item['observacao']}")

    with st.form("form_edicao_detalhe"):
        c1, c2 = st.columns(2)
        # Campos idênticos ao formulário de cadastro
        novo_nf = c1.text_input("Número NF", value=item['numero_nf'], disabled=not pode_editar)
        novo_cliente = c2.text_input("Cliente", value=item['cliente'], disabled=not pode_editar)
        
        tipo_opcoes = ["Diaria", "Devolução", "Paletização", "Pernoite", "Ajudante"]
        idx_tipo = tipo_opcoes.index(item['tipo_custo']) if item['tipo_custo'] in tipo_opcoes else 0
        novo_tipo = c1.selectbox("Tipo Custo", options=tipo_opcoes, index=idx_tipo, disabled=not pode_editar)
        novo_valor = c2.number_input("Valor (R$)", value=float(item['valor']), step=0.01, disabled=not pode_editar)
        
        # Tratamento de datas para o calendário do Streamlit
        dt_emissao_val = datetime.strptime(item['data_emissao_nf'], '%Y-%m-%d').date() if item.get('data_emissao_nf') else datetime.now().date()
        dt_entrega_val = datetime.strptime(item['data_entrega_nf'], '%Y-%m-%d').date() if item.get('data_entrega_nf') else datetime.now().date()
        
        novo_emissao = c1.date_input("Emissão NF", value=dt_emissao_val, disabled=not pode_editar)
        novo_entrega = c2.date_input("Entrega NF", value=dt_entrega_val, disabled=not pode_editar)
        
        st.write("**Arquivos Anexados:**")
        if item['comprovante_url']:
            for idx, url in enumerate(item['comprovante_url']):
                st.link_button(f"🔗 Ver Documento {idx+1}", url)
            
        if pode_editar:
            st.markdown("---")
            st.info("💡 Você pode corrigir os campos acima e anexar novos arquivos para reenviar.")
            novos_up = st.file_uploader("Adicionar novos arquivos", accept_multiple_files=True)
            
            if st.form_submit_button("✅ Salvar Alterações e Reenviar", type="primary"):
                payload = {
                    "numero_nf": novo_nf,
                    "cliente": novo_cliente,
                    "tipo_custo": novo_tipo,
                    "valor": novo_valor,
                    "data_emissao_nf": str(novo_emissao),
                    "data_entrega_nf": str(novo_entrega),
                    "status": "Aberto",
                    "observacao": None
                }
                if novos_up:
                    urls_novas = upload_arquivos(novos_up)
                    payload["comprovante_url"] = item['comprovante_url'] + urls_novas
                
                db.table("solicitacoes").update(payload).eq("id", item['id']).execute()
                st.success("Solicitação atualizada e reenviada!")
                st.rerun()
        else:
            if st.form_submit_button("Fechar"):
                st.rerun()

# --- VIEW PRINCIPAL ---
def render():
    # CSS Customizado Linea Alimentos
    st.markdown("""
        <style>
        .main h1 { color: #002D58; }
        div.stButton > button { height: 75px; border-radius: 10px; font-weight: bold; }
        button[key="f_todos"] { background-color: #002D58 !important; color: white !important; }
        button[key="f_pendente"] { background-color: #E30613 !important; color: white !important; }
        button[key="f_analise"] { background-color: #009FE3 !important; color: white !important; }
        button[key="f_faturado"] { background-color: #28A745 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚚 Painel do Transportador")
    st.caption(f"Portal de Custos Logísticos - Linea Alimentos | {st.session_state['email']}")

    if "filtro_status" not in st.session_state:
        st.session_state.filtro_status = "Todos"

    # Busca dados
    try:
        response = db.table("solicitacoes").select("*").eq("user_id", st.session_state["user"].id).order("id", desc=True).execute()
        df = pd.DataFrame(response.data)
    except:
        st.error("Erro ao carregar dados.")
        return

    # --- FILTROS (KPIs CLICÁVEIS) ---
    if not df.empty:
        cols = st.columns(4)
        if cols[0].button(f"🔵 TODOS\n{len(df)}", key="f_todos"): st.session_state.filtro_status = "Todos"
        pen = len(df[df['status'] == 'Pendente Documentos'])
        if cols[1].button(f"🔴 PENDENTES\n{pen}", key="f_pendente"): st.session_state.filtro_status = "Pendente Documentos"
        ana = len(df[df['status'] == 'Aberto'])
        if cols[2].button(f"🟡 ANÁLISE\n{ana}", key="f_analise"): st.session_state.filtro_status = "Aberto"
        fat = len(df[df['faturado'] == True])
        if cols[3].button(f"🟢 FATURADOS\n{fat}", key="f_faturado"): st.session_state.filtro_status = "Finalizado"

    # --- NOVA SOLICITAÇÃO (ESPELHANDO A IMAGEM DO QUADRO VERMELHO) ---
    with st.expander("➕ Nova Solicitação", expanded=False):
        with st.form("form_nova_linea", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nf = c1.text_input("Número NF")
            cliente = c2.text_input("Cliente")
            tipo = c1.selectbox("Tipo Custo", ["Diaria", "Devolução", "Paletização", "Pernoite", "Ajudante"])
            valor = c2.number_input("Valor (R$)", min_value=0.0, step=0.01)
            dt_emissao = c1.date_input("Emissão NF")
            dt_entrega = c2.date_input("Entrega NF")
            arquivos = st.file_uploader("Comprovante (PDF/JPG)", accept_multiple_files=True)
            
            if st.form_submit_button("Enviar Solicitação", type="primary"):
                if nf and cliente and arquivos:
                    urls = upload_arquivos(arquivos)
                    if urls:
                        payload = {
                            "user_id": st.session_state["user"].id,
                            "solicitante_email": st.session_state["email"],
                            "numero_nf": nf, "cliente": cliente, "tipo_custo": tipo, "valor": valor,
                            "data_emissao_nf": str(dt_emissao), "data_entrega_nf": str(dt_entrega),
                            "comprovante_url": urls, "status": "Aberto"
                        }
                        db.table("solicitacoes").insert(payload).execute()
                        st.success("Enviado com sucesso!")
                        st.rerun()

    # --- LISTA FILTRADA ---
    st.divider()
    df_filtrado = df if st.session_state.filtro_status == "Todos" else df[df['status'] == st.session_state.filtro_status]
    st.subheader(f"Lista: {st.session_state.filtro_status}")
    
    if not df_filtrado.empty:
        c_sel, c_btn = st.columns([3, 1])
        selecionado = c_sel.selectbox("Selecione para ver detalhes ou editar:", df_filtrado.index, 
                                     format_func=lambda x: f"NF: {df_filtrado.loc[x, 'numero_nf']} | {df_filtrado.loc[x, 'cliente']}")
        
        if c_btn.button("🔍 Ver Detalhes / Editar", use_container_width=True):
            modal_detalhes(df_filtrado.loc[selecionado].to_dict())

        st.dataframe(
            df_filtrado,
            column_config={
                "id": None, # Esconde o ID técnico
                "user_id": None, 
                "solicitante_email": None,
                "created_at": st.column_config.DatetimeColumn(
                    "Data Solicitação", 
                    format="DD/MM/YYYY HH:mm" # Formato Brasil
                ),
                "numero_nf": "NF",
                "cliente": "Cliente",
                "tipo_custo": "Tipo",
                "valor": st.column_config.NumberColumn(
                    "Valor (R$)", 
                    format="R$ %.2f"
                ),
                "data_emissao_nf": st.column_config.DateColumn(
                    "Emissão", 
                    format="DD/MM/YYYY" # Data sem hora
                ),
                "data_entrega_nf": st.column_config.DateColumn(
                    "Entrega", 
                    format="DD/MM/YYYY" # Data sem hora
                ),
                "status": "Status Atual",
                "comprovante_url": None, # Escondemos a URL bruta
                "observacao": "Motivo/Obs"
            },
            hide_index=True, 
            use_container_width=True
        )