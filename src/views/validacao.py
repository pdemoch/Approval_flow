import streamlit as st
import pandas as pd
from src.database import db
from datetime import datetime

# --- FUNÇÃO PARA SALVAR HISTÓRICO (Nova) ---
def salvar_historico(solicitacao_id, status, observacao):
    try:
        db.table("historico").insert({
            "solicitacao_id": solicitacao_id,
            "status_na_epoca": status,
            "observacao": observacao,
            "usuario_email": st.session_state["email"]
        }).execute()
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {e}")

# --- MODAL DE AÇÃO (Aprovar/Reprovar) ---
@st.dialog("⚖️ Analisar Solicitação")
def modal_analise(item):
    st.write(f"### NF: {item['numero_nf']} - {item['cliente']}")
    st.write(f"**Transportador:** {item['solicitante_email']}")
    
    c1, c2 = st.columns(2)
    c1.write(f"**Tipo:** {item['tipo_custo']}")
    c2.write(f"**Valor:** R$ {item['valor']:.2f}")
    
    dt_emissao = datetime.strptime(item['data_emissao_nf'], '%Y-%m-%d').strftime('%d/%m/%Y')
    dt_entrega = datetime.strptime(item['data_entrega_nf'], '%Y-%m-%d').strftime('%d/%m/%Y')
    c1.write(f"**Emissão:** {dt_emissao}")
    c2.write(f"**Entrega:** {dt_entrega}")

    st.write("**Documentos anexados:**")
    if item['comprovante_url']:
        for idx, url in enumerate(item['comprovante_url']):
            st.link_button(f"📄 Abrir Comprovante {idx+1}", url)

    st.divider()
    
    st.subheader("📜 Histórico da Solicitação")
    
    try:
        # Busca o histórico vinculado a esta solicitação
        hist_res = db.table("historico").select("*").eq("solicitacao_id", item['id']).order("created_at", desc=True).execute()
        
        if hist_res.data:
            for h in hist_res.data:
                # Formata a data para o padrão BR
                dt_h = datetime.fromisoformat(h['created_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                
                # Estilização visual de cada "evento"
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    c1.caption(f"⏰ {dt_h}")
                    c1.caption(f"👤 {h['usuario_email'].split('@')[0]}") # Mostra só o início do e-mail
                    
                    # Define a cor do status para facilitar a leitura
                    status_cor = "🔴" if "Pendente" in h['status_na_epoca'] else "🟢" if "Aprovado" in h['status_na_epoca'] else "🔵"
                    
                    c2.markdown(f"**{status_cor} {h['status_na_epoca']}**")
                    if h['observacao']:
                        c2.info(f"{h['observacao']}")
        else:
            st.write("Nenhum registro encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
    
    obs = st.text_area("Observações (obrigatório para Pendência ou Recusa)", placeholder="Digite o motivo aqui...")
    
    col1, col2, col3 = st.columns(3)
    
    # Botão APROVAR
    if col1.button("✅ Aprovar", use_container_width=True, type="primary"):
        db.table("solicitacoes").update({
            "status": "Aprovado",
            "validador_email": st.session_state["email"],
            "data_validacao": str(datetime.now())
        }).eq("id", item['id']).execute()
        
        # LOG DE HISTÓRICO
        salvar_historico(item['id'], "Aprovado", "Solicitação aprovada.")
        
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
            
            # LOG DE HISTÓRICO
            salvar_historico(item['id'], "Pendente Documentos", obs)
            
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
            
            # LOG DE HISTÓRICO
            salvar_historico(item['id'], "Recusada", obs)
            
            st.error("Solicitação Recusada.")
            st.rerun()

# --- VIEW PRINCIPAL ---
def render():
    st.title("⚖️ Painel de Validação")
    st.caption(f"Validador logado: {st.session_state['email']}")

    try:
        response = db.table("solicitacoes").select("*").eq("status", "Aberto").order("id", desc=True).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    if not df.empty:
        st.subheader(f"Fila de Análise ({len(df)})")
        
        c_sel, c_btn = st.columns([3, 1])
        selecionado = c_sel.selectbox(
            "Selecione uma solicitação para analisar:",
            df.index,
            format_func=lambda x: f"NF: {df.loc[x, 'numero_nf']} | {df.loc[x, 'cliente']} | R$ {df.loc[x, 'valor']:.2f}"
        )
        
        if c_btn.button("🔍 Analisar Agora", use_container_width=True):
            modal_analise(df.loc[selecionado].to_dict())

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
                "data_validacao": st.column_config.DatetimeColumn("Data Validação", format="DD/MM/YYYY HH:mm"),
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