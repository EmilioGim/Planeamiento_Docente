# data_loaders.py
import streamlit as st
from datetime import date, timedelta, datetime
from constants import dias_semana # Importar dias_semana desde constants

def load_general_parameters():
    st.markdown(
        """
        <style>
        .stDateInput label, .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label {
            font-weight: bold;
            color: #2c3e50;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    cols_general = st.columns(3)
    with cols_general[0]:
        fecha_inicio = st.date_input("Fecha inicio de clases:", value=date.today(), format="DD/MM/YYYY")
    with cols_general[1]:
        fecha_fin = st.date_input("Fecha fin de clases:", value=date.today() + timedelta(weeks=18), format="DD/MM/YYYY")
    with cols_general[2]:
        dia_clase = st.selectbox("Día de la semana:", options=list(dias_semana.keys()), index=0)
    return fecha_inicio, fecha_fin, dia_clase

def load_special_dates():
    col_feriado_input, col_feriado_btn = st.columns([0.7, 0.3])

    if 'feriados_list' not in st.session_state:
        st.session_state.feriados_list = []

    with col_feriado_input:
        feriado_date = st.date_input("Agregar feriados:", value=date.today(), key="add_feriado_date", format="DD/MM/YYYY")
    with col_feriado_btn:
        st.markdown("<br>", unsafe_allow_html=True) # Espaciador para alinear
        feriado_btn_pressed = st.button("➕ Agregar feriado", key="add_feriado_btn")

    feriado_to_remove = None
    remove_feriado_btn_pressed = False
    if st.session_state.feriados_list:
        feriado_to_remove = st.selectbox(
            "Seleccione un feriado para quitar:",
            options=[f.strftime('%d/%m/%Y') for f in st.session_state.feriados_list],
            key="remove_feriado_select"
        )
        remove_feriado_btn_pressed = st.button("➖ Quitar feriado seleccionado", key="remove_feriado_btn", help="Quita el feriado seleccionado de la lista.")

    st.subheader("Fechas de Pruebas")
    cols_pruebas = st.columns(3)
    with cols_pruebas[0]:
        prueba1_date = st.date_input("Fecha Prueba 1:", value=date.today() + timedelta(weeks=6), format="DD/MM/YYYY")
    with cols_pruebas[1]:
        prueba2_date = st.date_input("Fecha Prueba 2:", value=date.today() + timedelta(weeks=12), format="DD/MM/YYYY")
    with cols_pruebas[2]:
        examen_final_date = st.date_input("Fecha Examen Final:", value=date.today() + timedelta(weeks=17), format="DD/MM/YYYY")

    return feriado_date, feriado_btn_pressed, feriado_to_remove, remove_feriado_btn_pressed, \
           prueba1_date, prueba2_date, examen_final_date

def load_academic_units():
    num_unidades = st.number_input(
        "Número de unidades:",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="Define la cantidad de unidades académicas a planificar."
    )

    if 'unidades_data' not in st.session_state:
        st.session_state.unidades_data = [{'title': f'Unidad {i+1}', 'content': ''} for i in range(num_unidades)]
    elif len(st.session_state.unidades_data) != num_unidades:
        current_len = len(st.session_state.unidades_data)
        if num_unidades > current_len:
            for i in range(current_len, num_unidades):
                st.session_state.unidades_data.append({'title': f'Unidad {i+1}', 'content': ''})
        else:
            st.session_state.unidades_data = st.session_state.unidades_data[:num_unidades]

    unidades_input = []
    for i in range(num_unidades):
        with st.expander(f"Unidad {i+1}", expanded=False):
            st.session_state.unidades_data[i]['title'] = st.text_input(
                f"Título Unidad {i+1}:",
                value=st.session_state.unidades_data[i]['title'],
                key=f"unit_title_{i}"
            )
            st.session_state.unidades_data[i]['content'] = st.text_area(
                f"Contenido Unidad {i+1}:",
                value=st.session_state.unidades_data[i]['content'],
                height=100,
                key=f"unit_content_{i}"
            )
        title = st.session_state.unidades_data[i]['title'].strip()
        contents = st.session_state.unidades_data[i]['content'].strip()
        if title and contents:
            unidades_input.append((title, contents))
    return unidades_input