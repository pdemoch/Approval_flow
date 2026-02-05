from supabase import create_client
import streamlit as st
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def login():
    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user is None:
            st.error("Falha no login. Verifique email e senha.")
            return

        st.session_state["user"] = response.user
        st.session_state["authenticated"] = True
        st.rerun()
