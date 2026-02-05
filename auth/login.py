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
        try:
            user = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            st.session_state["user"] = user.user
            st.session_state["authenticated"] = True
            st.experimental_rerun()

        except Exception:
            st.error("Usuário ou senha inválidos")
