import streamlit as st
from src.database import db
import pandas as pd

def render():
    st.title("💰 Painel de Faturamento")
    
    # Busca apenas o que precisa ser faturado
    response = db.table("solicitacoes").select("*").eq("status", "Faturar").eq("faturado", False).execute()
    
    if not response.data:
        st.info("Nada para faturar no momento.")
        return
        
    df = pd.DataFrame(response.data)
    
    # Adiciona coluna de seleção
    df_editor = df.copy()
    df_editor["Selecionar"] = False
    
    # Exibe tabela editável
    st.write("Selecione os itens para gerar o lote de faturamento:")
    edited_df = st.data_editor(
        df_editor,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(required=True),
            "comprovante_url": st.column_config.LinkColumn("Comprovante")
        },
        disabled=["id", "numero_nf", "cliente", "valor"],
        hide_index=True
    )
    
    # Processamento em lote
    st.divider()
    col1, col2 = st.columns([3, 1])
    id_fatura = col1.text_input("ID da Fatura / Lote")
    
    if col2.button("Processar Faturamento"):
        selecionados = edited_df[edited_df["Selecionar"] == True]
        
        if selecionados.empty:
            st.warning("Selecione pelo menos um item.")
        elif not id_fatura:
            st.warning("Informe o ID da Fatura.")
        else:
            ids_para_atualizar = selecionados["id"].tolist()
            
            # Atualização em massa
            db.table("solicitacoes").update({
                "status": "Finalizado",
                "faturado": True,
                "id_fatura": id_fatura
            }).in_("id", ids_para_atualizar).execute()
            
            st.success(f"Fatura {id_fatura} gerada para {len(ids_para_atualizar)} itens!")
            st.rerun()