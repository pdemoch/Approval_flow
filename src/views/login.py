import streamlit as st
from src.database import db
import time

def render():
    st.markdown("## 🔐 Acesso ao Sistema")
    
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar", type="primary"):
        try:
            auth_response = db.auth.sign_in_with_password({"email": email, "password": password})
            user = auth_response.user
            
            # Busca o perfil (Role)
            profile = db.table("profiles").select("*").eq("id", user.id).single().execute()
            
            if profile.data:
                st.session_state["user"] = user
                st.session_state["role"] = profile.data["role"]
                st.session_state["email"] = email
                st.success("Login realizado! Redirecionando...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Perfil de usuário não encontrado.")
                
        except Exception as e:
            st.error(f"Erro ao logar: {e}")