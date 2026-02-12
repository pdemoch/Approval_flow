import streamlit as st
import pandas as pd
from src.database import db
from datetime import datetime
import uuid

# Função auxiliar para upload de lista de arquivos
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
            # Pega URL publica
            public_url = db.storage.from_(bucket).get_public_url(file_name)
            urls.append(public_url)
        except Exception as e:
            st.error(f"Erro ao fazer upload de {arquivo.name}: {e}")
            return None
    return urls

def render():
    # --- CABEÇALHO ---
    st.title("🚚 Painel do Transportador")
    st.caption(f"Logado como: {st.session_state['email']}")

    # Busca dados atualizados
    try:
        response = db.table("solicitacoes").select("*").eq("user_id", st.session_state["user"].id).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error("Erro de conexão com banco de dados")
        return

    # --- DASHBOARD (KPIs) ---
    if not df.empty:
        st.subheader("Visão Geral")
        
        # Cálculos
        total = len(df)
        abertos = len(df[df['status'] == 'Aberto'])
        pendentes = len(df[df['status'] == 'Pendente Documentos'])
        recusados = len(df[df['status'] == 'Recusada'])
        faturados = len(df[df['faturado'] == True])
        
        # Cards de Métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total", total)
        col2.metric("Abertos", abertos, delta_color="off")
        col3.metric("Pendentes", pendentes, delta="-Atenção", delta_color="inverse")
        col4.metric("Recusados", recusados, delta="-Pare", delta_color="inverse")
        col5.metric("Faturados", faturados, delta="Sucesso")
        
        st.divider()

    # --- ÁREA DE AÇÃO URGENTE (PENDÊNCIAS) ---
    # Se tiver algo pendente, mostramos primeiro com destaque!
    pendencias_df = df[df['status'] == 'Pendente Documentos'] if not df.empty else pd.DataFrame()
    
    if not pendencias_df.empty:
        st.warning(f"⚠️ Você tem {len(pendencias_df)} solicitações precisando de correção!")
        
        for index, row in pendencias_df.iterrows():
            with st.expander(f"🔴 CORRIGIR: NF {row['numero_nf']} - {row['cliente']}", expanded=True):
                c1, c2 = st.columns([2, 1])
                c1.error(f"**Motivo da Pendência:** {row.get('observacao', 'Sem observação registrada.')}")
                c2.write(f"**Valor:** R$ {row['valor']}")
                
                with st.form(key=f"fix_form_{row['id']}"):
                    st.write("Anexe os documentos corretos/faltantes:")
                    novos_arquivos = st.file_uploader("Novos Comprovantes", accept_multiple_files=True, key=f"up_{row['id']}")
                    
                    if st.form_submit_button("Enviar Correção"):
                        if novos_arquivos:
                            urls_novas = upload_arquivos(novos_arquivos)
                            if urls_novas:
                                # Atualiza status para Aberto novamente e salva novas URLs
                                db.table("solicitacoes").update({
                                    "status": "Aberto",
                                    "comprovante_url": urls_novas, # Sobrescreve ou concatena (aqui estou sobrescrevendo para limpar o erro)
                                    "observacao": None # Limpa a observação antiga
                                }).eq("id", row['id']).execute()
                                st.success("Correção enviada! O item voltou para análise.")
                                st.rerun()
                        else:
                            st.warning("Você precisa anexar arquivos para corrigir.")

    # --- FORMULÁRIO DE NOVA SOLICITAÇÃO ---
    with st.expander("➕ Nova Solicitação", expanded=False):
        with st.form("form_solicitacao", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nf = col1.text_input("Número NF")
            cliente = col2.text_input("Cliente")
            tipo = col1.selectbox("Tipo Custo", ["Diaria", "Devolução", "Paletização", "Pernoite"])
            valor = col2.number_input("Valor (R$)", min_value=0.0, step=0.01)
            dt_emissao = col1.date_input("Emissão NF")
            dt_entrega = col2.date_input("Entrega NF")
            
            # Múltiplos Arquivos
            arquivos = st.file_uploader("Comprovantes (PDF/JPG)", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)
            
            if st.form_submit_button("Enviar Solicitação", type="primary"):
                if not (nf and cliente and arquivos):
                    st.error("Preencha todos os campos e anexe pelo menos um comprovante.")
                else:
                    urls = upload_arquivos(arquivos)
                    if urls:
                        payload = {
                            "user_id": st.session_state["user"].id,
                            "solicitante_email": st.session_state["email"],
                            "numero_nf": nf,
                            "cliente": cliente,
                            "tipo_custo": tipo,
                            "valor": valor,
                            "data_emissao_nf": str(dt_emissao),
                            "data_entrega_nf": str(dt_entrega),
                            "comprovante_url": urls, # Agora salva lista
                            "status": "Aberto"
                        }
                        try:
                            db.table("solicitacoes").insert(payload).execute()
                            st.success("Solicitação criada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar no banco: {e}")

    # --- TABELA HISTÓRICO ---
    st.divider()
    st.subheader("Minhas Solicitações")

    if not df.empty:
        # Preparando visualização
        df_view = df.copy()
        
        # Configuração da tabela bonita
        st.dataframe(
            df_view,
            column_config={
                "id": None, # Esconde ID
                "user_id": None, # Esconde User ID
                "solicitante_email": None, # Ele já sabe o email dele
                "created_at": st.column_config.DatetimeColumn("Criado em", format="D/M/Y HH:mm"),
                "data_emissao_nf": st.column_config.DateColumn("Emissão"),
                "data_entrega_nf": st.column_config.DateColumn("Entrega"),
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "status": st.column_config.Column(
                    "Status",
                    help="Status atual do processo",
                    width="medium",
                ),
                "comprovante_url": st.column_config.ListColumn("Arquivos"), # Mostra como lista
                "observacao": st.column_config.TextColumn("Observações Validador"),
                "faturado": st.column_config.CheckboxColumn("Faturado?")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Nenhum registro encontrado.")