# auth.py
import streamlit as st

def login_screen():
    """
    Muestra la pantalla de inicio de sesión y maneja la autenticación.
    Retorna True si el usuario ha iniciado sesión, False de lo contrario.
    """
    st.title("Iniciar Sesión")

    # Inicializar el estado de la sesión para el login si no está presente
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None # 'standard' o 'premium'

    if st.session_state.logged_in:
        return True # Si ya está logueado, no mostrar la pantalla de login

    login_choice = st.radio("Seleccione tipo de usuario:", ("Usuario Estándar", "Usuario Premium"), key="login_choice")

    if login_choice == "Usuario Estándar":
        if st.button("Continuar como Usuario Estándar", key="standard_login_btn"):
            st.session_state.logged_in = True
            st.session_state.user_type = 'standard'
            st.rerun() # Volver a ejecutar para mostrar la aplicación principal
        return False
    else: # Usuario Premium
        username = st.text_input("Usuario:", key="username_input")
        password = st.text_input("Contraseña:", type="password", key="password_input")

        # Importar PREMIUM_USERS aquí para evitar una posible dependencia circular si constants importara auth
        from constants import PREMIUM_USERS

        if st.button("Iniciar Sesión como Premium", key="premium_login_btn"):
            if username in PREMIUM_USERS and PREMIUM_USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.user_type = 'premium'
                st.success(f"Bienvenido, {username}! Has iniciado sesión como usuario Premium.")
                st.rerun() # Volver a ejecutar para mostrar la aplicación principal
            else:
                st.error("Usuario o contraseña incorrectos.")
        return False

def logout_button():
    """
    Muestra un botón de cerrar sesión en la barra lateral si el usuario está logueado.
    """
    if st.session_state.get('logged_in'):
        if st.sidebar.button("Cerrar Sesión", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.info("Sesión cerrada.")
            st.rerun() # Volver a ejecutar para regresar a la pantalla de login