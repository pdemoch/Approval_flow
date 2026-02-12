import streamlit as st
import pandas as pd
from src.database import db
from datetime import datetime

# --- MODAL DE AÇÃO (Aprovar/Reprovar) ---
@st.dialog("⚖️ Analisar Solicitação")
def modal_analise(item):
    st.write(f"### NF: {item['numero_nf']} - {item['cliente']}")
    st.write(f"**Transportador:** {item['solicitante_email']}")
    
    # Exibição dos dados
    c1, c2 = st.columns(2)
    c1.write(f"**Tipo:** {item['tipo_custo']}")
    c2.write(f"**Valor:** R$ {item['valor']:.2f}")
    
    # Formatação de datas apenas para visualização no Modal
    dt_emissao = datetime.strptime(item['data_emissao_nf'], '%Y-%m-%d').strftime('%d/%m/%Y')
    dt_entrega = datetime.strptime(item['data_entrega_nf'], '%Y-%m-%d').strftime('%d/%m/%Y')
    c1.write(f"**Emissão:** {dt_emissao}")
    c2.write(f"**Entrega:** {dt_entrega}")

    st.write("**Documentos anexados:**")
    if item['comprovante_url']:
        for idx, url in enumerate(item['comprovante_url']):
            st.link_button(f"📄 Abrir Comprovante {idx+1}", url)

    st.divider()
    
    obs = st.text_area("Observações (obrigatório para Pendência ou Recusa)", placeholder="Digite o motivo aqui...")
    
    col1, col2, col3 = st.columns(3)
    
    # Botão APROVAR
    if col1.button("✅ Aprovar", use_container_width=True, type="primary"):
        db.table("solicitacoes").update({
            "status": "Aprovado",
            "validador_email": st.session_state["email"],
            "data_validacao": str(datetime.now())
        }).eq("id", item['id']).execute()
        st.success("Solicitação Aprovada!")
        st.rerun()

    # Botão PENDÊNCIA
    if col2.button("⚠️ Pendência", use_container_width=True):
        if not obs:
            st.warning("⚠️ Descreva o motivo da pendência no campo de observações.")
        else:
            db.table("solicitacoes").update({
                "status": "Pendente Documentos",
                "observacao": obs,
                "validador_email": st.session_state["email"],
                "data_validacao": str(datetime.now())
            }).eq("id", item['id']).execute()
            st.info("Solicitação devolvida para correção.")
            st.rerun()

    # Botão RECUSAR
    if col3.button("❌ Recusar", use_container_width=True):
        if not obs:
            st.warning("⚠️ Descreva o motivo da recusa no campo de observações.")
        else:
            db.table("solicitacoes").update({
                "status": "Recusada",
                "observacao": obs,
                "validador_email": st.session_state["email"],
                "data_validacao": str(datetime.now())
            }).eq("id", item['id']).execute()
            st.error("Solicitação Recusada.")
            st.rerun()

# --- VIEW PRINCIPAL ---
def render():
    st.title("⚖️ Painel de Validação")
    st.caption(f"Validador logado: {st.session_state['email']}")

    # 1. BUSCA FILTRADA: Apenas status 'Aberto'
    try:
        response = db.table("solicitacoes").select("*").eq("status", "Aberto").order("id", desc=True).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    if not df.empty:
        st.subheader(f"Fila de Análise ({len(df)})")
        
        # Seletor para abrir o Modal
        c_sel, c_btn = st.columns([3, 1])
        selecionado = c_sel.selectbox(
            "Selecione uma solicitação para analisar:",
            df.index,
            format_func=lambda x: f"NF: {df.loc[x, 'numero_nf']} | {df.loc[x, 'cliente']} | R$ {df.loc[x, 'valor']:.2f}"
        )
        
        if c_btn.button("🔍 Analisar Agora", use_container_width=True):
            modal_analise(df.loc[selecionado].to_dict())

        # 2. TABELA CONFIGURADA
        st.dataframe(
            df,
            column_config={
                "id": None, 
                "user_id": None,
                "created_at": st.column_config.DatetimeColumn("Data Solicitação", format="DD/MM/YYYY HH:mm"),
                "solicitante_email": "Transportador",
                "numero_nf": "NF",
                "cliente": "Cliente",
                "tipo_custo": "Tipo",
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "data_emissao_nf": st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"),
                "data_entrega_nf": st.column_config.DateColumn("Entrega", format="DD/MM/YYYY"),
                "status": "Status",
                "validador_email": "Validado Por",
                
                # 3. Formatação Data Validação (igual Solicitação)
                "data_validacao": st.column_config.DatetimeColumn("Data Validação", format="DD/MM/YYYY HH:mm"),
                
                # Ocultando as colunas solicitadas
                "faturado": None,
                "id_fatura": None,
                "comprovante_url": None, 
                "observacao": "Observação"
            },
            hide_index=True, 
            use_container_width=True
        )
    else:
        st.success("🎉 Tudo limpo! Nenhuma solicitação pendente de análise no momento.")