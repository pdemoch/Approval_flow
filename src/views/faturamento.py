import streamlit as st
import pandas as pd
from src.database import db
from datetime import datetime
import uuid

# --- FUNÇÃO DE HISTÓRICO ---
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

# --- VIEW PRINCIPAL ---
def render():
    st.title("💰 Painel de Faturamento")
    st.caption(f"Financeiro: {st.session_state['email']} | Processamento de Pagamentos")

    # 1. BUSCA DADOS (Somente Aprovados e Não Faturados)
    try:
        res = db.table("solicitacoes").select("*")\
            .eq("status", "Aprovado")\
            .eq("faturado", False)\
            .order("id", desc=True).execute()
        df = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    if df.empty:
        st.success("✅ Nenhuma solicitação pendente de faturamento. Bom trabalho!")
        return

    # 2. RESUMO FINANCEIRO
    total_pendente = df['valor'].sum()
    st.metric("Total Aprovado para Pagamento", f"R$ {total_pendente:,.2f}")

    st.divider()
    st.subheader("📦 Agrupamento de Lote")
    st.info("Selecione as solicitações abaixo para gerar um novo lote de faturamento.")

    # 3. INTERFACE DE SELEÇÃO (Data Editor com Checkbox)
    # Adicionamos uma coluna temporária para seleção
    df.insert(0, "Selecionar", False)
    
    # Configuração da tabela para ser editável apenas na coluna de seleção
    df_editado = st.data_editor(
        df,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(help="Marque para faturar"),
            "id": None, "user_id": None, "comprovante_url": None, "faturado": None, "id_fatura": None,
            "created_at": st.column_config.DatetimeColumn("Data Solicitação", format="DD/MM/YYYY"),
            "numero_nf": "NF", "cliente": "Cliente", "tipo_custo": "Tipo",
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "solicitante_email": "Transportador",
            "validador_email": "Aprovado por",
            "data_validacao": st.column_config.DatetimeColumn("Data Aprovação", format="DD/MM/YYYY")
        },
        disabled=[c for c in df.columns if c != "Selecionar"],
        hide_index=True,
        use_container_width=True
    )

    # 4. PROCESSAMENTO DO LOTE
    itens_selecionados = df_editado[df_editado["Selecionar"] == True]
    
    if not itens_selecionados.empty:
        qtd = len(itens_selecionados)
        soma = itens_selecionados['valor'].sum()
        
        st.warning(f"🔔 **{qtd}** notas selecionadas. Total do Lote: **R$ {soma:,.2f}**")
        
        with st.form("form_faturamento"):
            # Deixamos o valor padrão vazio para forçar o preenchimento manual
            cod_lote = st.text_input("📝 Digite o Código Interno do Lote (Obrigatório)", value="")
            
            st.caption("Exemplo: Nº do SAP, Ordem de Pagamento ou Código do Banco.")

            if st.form_submit_button("🚀 Finalizar Faturamento e Gerar Lote", type="primary"):
                # VALIDAÇÃO: Se o código estiver vazio, não prossegue
                if not cod_lote:
                    st.error("❌ Erro: Você precisa informar o **Código Interno** para finalizar o faturamento.")
                else:
                    ids_para_atualizar = itens_selecionados['id'].tolist()
                    
                    try:
                        # Atualiza todas as solicitações selecionadas no banco
                        db.table("solicitacoes").update({
                            "faturado": True,
                            "id_fatura": cod_lote, # Aqui entra o seu código interno
                            "status": "Finalizado"
                        }).in_("id", ids_para_atualizar).execute()
                        
                        # Salva no histórico de cada uma para rastreabilidade
                        for id_sol in ids_para_atualizar:
                            salvar_historico(
                                id_sol, 
                                "Finalizado", 
                                f"Faturamento concluído. Código Interno: {cod_lote}"
                            )
                        
                        st.success(f"✅ Lote {cod_lote} finalizado e registrado com sucesso!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao processar faturamento: {e}")
    else:
        st.write("👆 Marque os itens na tabela para prosseguir.")