# output_generators.py
import streamlit as st
import io
import base64
import requests # Importar la librería requests

# Importación condicional de DocxTemplate, ya que no se usa en todas las funciones
try:
    from docxtpl import DocxTemplate
except ImportError:
    st.warning("La librería 'python-docx-template' no está instalada. La generación de documentos Word no estará disponible.")
    DocxTemplate = None # Establecer a None si no está disponible

def setup_streamlit_ui():
    st.set_page_config(
        page_title="Planeamiento Semestral - Bloom + Procesamiento Básico",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown(
        """
        <style>
        .reportview-container .main .block-container{
            padding-top: 2rem;
            padding-right: 2rem;
            padding-left: 2rem;
            padding-bottom: 2rem;
        }
        .stDateInput label, .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label {
            font-weight: bold;
            color: #2c3e50;
        }
        .stButton>button {
            background-color: #27ae60;
            color: white;
            font-weight: bold;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            border: none;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton>button:hover {
            background-color: #2ecc71;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }
        .stAlert {
            border-radius: 0.5rem;
        }
        .stDownloadButton>button {
            background-color: #2980b9;
        }
        .stDownloadButton>button:hover {
            background-color: #3498db;
        }
        .stExpander {
            border-radius: 0.5rem;
            border: 1px solid #ddd;
            padding: 1rem;
            margin-bottom: 0.5rem;
            background-color: #ecf0f1;
        }
        .stExpander div[data-baseweb="card"] {
            background-color: #ecf0f1;
        }
        .css-1r6dm7f {
            font-weight: bold;
            color: #2c3e50;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("📚 Planeamiento Semestral Bloom by emSoft")
    st.info("Complete los datos. Todas las fechas se eligen con el calendario. El examen final SIEMPRE es la sesión 17.")

    # Inicialización de session_state si no existen
    if 'feriados_list' not in st.session_state:
        st.session_state.feriados_list = []
    if 'generated_context' not in st.session_state:
        st.session_state.generated_context = None
    if 'generated_out_text' not in st.session_state:
        st.session_state.generated_out_text = None
    if 'plantilla_planeamiento_bytes' not in st.session_state:
        st.session_state.plantilla_planeamiento_bytes = None
    if 'plantilla_cronograma_bytes' not in st.session_state:
        st.session_state.plantilla_cronograma_bytes = None

def generate_text_output(fecha_inicio, fecha_fin, dia_clase, fechas_prueba,
                           fechas_sesiones, unidades, lista_sesiones_word, feriados_list):
    out = "\n📋 PLANIFICACIÓN SEMESTRAL\n"
    out += "=" * 90 + "\n"
    out += f"PERÍODO: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}\n"
    out += f"DÍA DE CLASE: {dia_clase.capitalize()}\n"

    if feriados_list:
        out += f"FERIADOS: {', '.join([f.strftime('%d/%m/%Y') for f in feriados_list])}\n"

    fechas_validas = [f for f in fechas_prueba if f in fechas_sesiones]
    if fechas_validas:
        out += f"PRUEBAS: {', '.join([f.strftime('%d/%m/%Y') for f in fechas_validas])}\n"

    out += f"EXAMEN FINAL: {fechas_sesiones[-1].strftime('%d/%m/%Y')}\n"
    out += "\n" + "-" * 90 + "\n"
    out += "UNIDADES PROGRAMADAS:\n"

    for i, unidad in enumerate(unidades, 1):
        out += f"{i}. {unidad['titulo']}\n"
        for contenido in unidad['lineas']:
            out += f"   - {contenido}\n"
        out += "\n"

    out += "=" * 90 + "\n"
    out += "\n📅 SESIONES DEL SEMESTRE:\n"

    for sesion in lista_sesiones_word:
        out += f"\n🔵 SESIÓN {sesion['Numero']:02d} | {sesion['Fecha']} | {sesion['Evento']}\n"
        out += "-" * 60 + "\n"

        if sesion["Evento"] == "Clase normal" and sesion["Planificacion"]:
            p = sesion["Planificacion"]
            out += f"UNIDAD : {p['Unidad']}\n"
            out += f"CONTENIDO: {p['Contenido']}\n"
            out += f"OBJETIVO: El estudiante será capaz de {p['Verbo']} {p['Concepto']}\n"
            out += f"Nivel Bloom: {p['Nivel']}\n"
            out += f"Estrategias de aprendizaje: {p['Actividad']}\n"
            out += f"Retroalimentación: {p['Retroalimentacion']}\n"
            out += f"Introducción: {p['Introduccion']}\n"
            out += f"Inicio: {p['Inicio']}\n"
            out += f"Desarrollo: {p['Desarrollo']}\n"
            out += f"Cierre: {p['Cierre']}\n"
            out += f"Recursos: {p['Recursos']}\n"
            out += f"Evaluación: {p['Evaluacion']}\n"

        if sesion["En_feriado"]:
            out += " ⚠️ ¡Advertencia! Esta sesión coincide con un feriado. Reagendar si es necesario.\n"

        out += "-" * 60 + "\n"

    return out

def generate_word_documents():
    # Define las URLs RAW de tus plantillas en GitHub
    # Asegúrate de que las URLs estén CORRECTAMENTE entre comillas dobles o simples.
    # Y que sean las URLs RAW (crudas) de los archivos.
    PLAN_TEMPLATE_URL = "https://github.com/EmilioGim/Planeamiento_Docente/raw/refs/heads/main/plantillas/Plantilla_planeamiento.docx"
    CRON_TEMPLATE_URL = "https://github.com/EmilioGim/Planeamiento_Docente/raw/refs/heads/main/plantillas/Plantilla_Cronograma.docx"

    # Eliminado: st.subheader("Cargando Plantillas Word desde GitHub")

    # Cargar plantilla de Planeamiento
    try:
        response_plan = requests.get(PLAN_TEMPLATE_URL)
        response_plan.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
        st.session_state.plantilla_planeamiento_bytes = response_plan.content
        # Eliminado: st.success(f"Plantilla de Planeamiento cargada exitosamente desde GitHub.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error al cargar la plantilla de Planeamiento desde GitHub: {e}. Por favor, verifica la URL.")
        st.session_state.plantilla_planeamiento_bytes = None

    # Cargar plantilla de Cronograma
    try:
        response_cron = requests.get(CRON_TEMPLATE_URL)
        response_cron.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
        st.session_state.plantilla_cronograma_bytes = response_cron.content
        # Eliminado: st.success(f"Plantilla de Cronograma cargada exitosamente desde GitHub.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error al cargar la plantilla de Cronograma desde GitHub: {e}. Por favor, verifica la URL.")
        st.session_state.plantilla_cronograma_bytes = None

    return None, None