import streamlit as st
from supabase import create_client, Client
import os

@st.cache_resource
def get_db() -> Client:
    # 1. Tenta pegar dos secrets (Streamlit Cloud/Local)
    # 2. Se não achar, tenta pegar das Variáveis de Ambiente (Render/Docker)
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    
    # Validação rigorosa antes de tentar conectar
    if not url or not key:
        st.error("🚨 Erro Crítico: As variáveis SUPABASE_URL e SUPABASE_KEY não foram encontradas.")
        st.info("No Render: Vá em Environment e adicione as chaves.")
        st.info("Localmente: Verifique o arquivo .streamlit/secrets.toml")
        st.stop()

    # Limpeza de strings (Remove aspas e espaços acidentais que causam o erro Invalid URL)
    url = url.strip().replace('"', '').replace("'", "")
    key = key.strip().replace('"', '').replace("'", "")

    # Tenta criar o cliente
    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        st.stop()

db = get_db()