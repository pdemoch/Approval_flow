import streamlit as st
from src.database import db
from datetime import datetime

def render():
    st.title("🛡️ Painel de Validação")
    
    # Filtros
    st.sidebar.header("Filtros")
    filtro_status = st.sidebar.selectbox("Filtrar Status", ["Todos", "Aberto", "Pendente Documentos"])
    
    query = db.table("solicitacoes").select("*").order("created_at", desc=True)
    if filtro_status != "Todos":
        query = query.eq("status", filtro_status)
    
    items = query.execute().data
    
    if not items:
        st.info("Nenhuma solicitação pendente.")
        return

    for item in items:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
            c1.write(f"**ID:** {item['id']}")
            c2.write(f"**NF:** {item['numero_nf']}")
            c3.write(f"**Cliente:** {item['cliente']}")
            c4.write(f"**Status:** `{item['status']}`")
            
            with st.expander(f"Detalhes ID {item['id']}"):
                st.write(f"**Valor:** R$ {item['valor']}")
                st.write(f"**Solicitante:** {item['solicitante_email']}")
                if item['comprovante_url']:
                    st.link_button("Ver Comprovante", item['comprovante_url'])
                
                # Ações
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                if col_btn1.button("Aprovar (Faturar)", key=f"apr_{item['id']}"):
                    db.table("solicitacoes").update({
                        "status": "Faturar",
                        "validador_email": st.session_state["email"],
                        "data_validacao": datetime.now().isoformat()
                    }).eq("id", item['id']).execute()
                    st.rerun()
                    
                if col_btn2.button("Pedir Documentos", key=f"doc_{item['id']}"):
                    db.table("solicitacoes").update({"status": "Pendente Documentos"}).eq("id", item['id']).execute()
                    st.rerun()

                if col_btn3.button("Recusar", key=f"rec_{item['id']}"):
                    db.table("solicitacoes").update({"status": "Recusada"}).eq("id", item['id']).execute()
                    st.rerun()