import streamlit as st
from supabase import create_client, Client
import os

@st.cache_resource
def get_db() -> Client:
    url = None
    key = None

    # 1. Tenta pegar dos secrets do Streamlit (envolvido em try para não quebrar no Render)
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        # Se st.secrets falhar (comum no Render sem arquivo .toml), url e key continuam None
        pass

    # 2. Se não achou nos secrets, tenta pegar das Variáveis de Ambiente do OS
    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_KEY")
    
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
        
# 1. Executa a função para pegar o cliente
db = get_db()

# 2. Cria um apelido chamado 'supabase' para o mesmo objeto
# Isso resolve o erro de importação no app.py e login.py
supabase = db