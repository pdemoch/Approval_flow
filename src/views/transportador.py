import streamlit as st
from src.database import db
from datetime import datetime
import uuid

def render():
    st.title(f"Painel Transportador: {st.session_state['email']}")
    
    # --- Formulário ---
    with st.expander("📝 Nova Solicitação", expanded=True):
        with st.form("form_solicitacao", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nf = col1.text_input("Número NF")
            cliente = col2.text_input("Cliente")
            tipo = col1.selectbox("Tipo Custo", ["Diaria", "Devolução", "Paletização", "Pernoite"])
            valor = col2.number_input("Valor (R$)", min_value=0.0, step=0.01)
            dt_emissao = col1.date_input("Emissão NF")
            dt_entrega = col2.date_input("Entrega NF")
            arquivo = st.file_uploader("Comprovante (PDF/JPG)", type=["pdf", "jpg", "jpeg"])
            
            if st.form_submit_button("Enviar Solicitação"):
                if not (nf and cliente and arquivo):
                    st.error("Preencha todos os campos e anexe o comprovante.")
                else:
                    try:
                        # 1. Upload Arquivo
                        file_ext = arquivo.name.split(".")[-1]
                        file_name = f"{uuid.uuid4()}.{file_ext}"
                        bucket = "comprovantes"
                        
                        db.storage.from_(bucket).upload(
                            path=file_name,
                            file=arquivo.getvalue(),
                            file_options={"content-type": arquivo.type}
                        )
                        
                        public_url = db.storage.from_(bucket).get_public_url(file_name)
                        
                        # 2. Insert no Banco
                        payload = {
                            "user_id": st.session_state["user"].id,
                            "solicitante_email": st.session_state["email"],
                            "numero_nf": nf,
                            "cliente": cliente,
                            "tipo_custo": tipo,
                            "valor": valor,
                            "data_emissao_nf": str(dt_emissao),
                            "data_entrega_nf": str(dt_entrega),
                            "comprovante_url": public_url,
                            "status": "Aberto"
                        }
                        
                        db.table("solicitacoes").insert(payload).execute()
                        st.success("Solicitação enviada com sucesso!")
                        
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # --- Tabela ---
    st.divider()
    st.subheader("Minhas Solicitações")
    
    # Query filtrando pelo ID do usuário logado
    response = db.table("solicitacoes").select("*").eq("user_id", st.session_state["user"].id).order("id", desc=True).execute()
    
    if response.data:
        st.dataframe(response.data)
    else:
        st.info("Nenhuma solicitação encontrada.")