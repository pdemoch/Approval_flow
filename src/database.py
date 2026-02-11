import streamlit as st
from supabase import create_client
import os

@st.cache_resource
def get_db():
    # Tenta pegar dos secrets (local) ou variaveis de ambiente (Render)
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url:
        st.error("Configuração de Banco de Dados não encontrada.")
        st.stop()
        
    return create_client(url, key)

db = get_db()