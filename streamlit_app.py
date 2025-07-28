import streamlit as st
from datetime import datetime, timedelta, date
import random
import re
from collections import Counter
import io
import base64

# Instalación y manejo de docxtpl para Streamlit (debe estar instalado en el entorno)
try:
    from docxtpl import DocxTemplate
except ImportError:
    st.error("La librería 'python-docx-template' no está instalada. Por favor, instálala usando: pip install python-docx-template")
    st.stop()

verbos_bloom = {
    "Recordar": ["identificar", "definir", "listar"],
    "Comprender": ["explicar", "resumir", "interpretar"],
    "Aplicar": ["resolver", "utilizar", "demostrar"],
    "Analizar": ["comparar", "diferenciar", "analizar"],
    "Evaluar": ["justificar", "juzgar", "concluir"],
    "Crear": ["diseñar", "elaborar", "idear"]
}

plantillas_actividades = {
    "Recordar": "Realizar un glosario con términos sobre '{}'.",
    "Comprender": "Redactar un resumen sobre '{}'.",
    "Aplicar": "Resolver un ejercicio práctico sobre '{}'.",
    "Analizar": "Analizar un caso relacionado con '{}'.",
    "Evaluar": "Justificar la relevancia de '{}'.",
    "Crear": "Diseñar una solución basada en '{}'."
}

recursos_bloom = {
    "Recordar": ["fichas", "presentación", "mapas simples"],
    "Comprender": ["lectura", "videos", "debate"],
    "Aplicar": ["simulador", "ejercicios", "laboratorio"],
    "Analizar": ["casos", "gráficos", "tablas"],
    "Evaluar": ["rúbricas", "informes", "discusión crítica"],
    "Crear": ["software", "proyecto", "portafolio"]
}

evaluacion_bloom = {
    "Recordar": ["test", "lista de cotejo"],
    "Comprender": ["resúmenes", "cuestionarios"],
    "Aplicar": ["demostraciones", "resolución de problemas"],
    "Analizar": ["ensayos", "mapas comparativos"],
    "Evaluar": ["defensa oral", "argumentación escrita"],
    "Crear": ["prototipo", "presentación final"]
}

inicio = ["Lluvia de ideas", "Pregunta generadora", "Video disparador"]
desarrollo = ["Actividad práctica", "Discusión guiada", "Resolución de caso"]
cierre = ["Mapa mental", "Reflexión", "Síntesis grupal"]
intro = ["Lectura disparadora", "Situación problema", "Contextualización narrativa"]
retro = ["Recordatorio de clase anterior", "Juego de revisión", "Preguntas orales"]
dias_semana = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4, "sábado": 5}

def extraer_conceptos_simple(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', ' ', texto)
    stop_words = {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
        'da', 'su', 'por', 'son', 'con', 'para', 'al', 'una', 'ser', 'las', 'del', 'los',
        'como', 'pero', 'sus', 'hay', 'está', 'han', 'si', 'más', 'me', 'ya', 'muy', 'o',
        'este', 'esta', 'están', 'puede', 'nos', 'todo', 'tiene', 'fue', 'entre', 'cuando',
        'hasta', 'desde', 'hacer', 'cada', 'porque', 'sobre', 'otros', 'tanto', 'tiempo',
        'donde', 'mismo', 'ahora', 'después', 'vida', 'también', 'sin', 'años', 'estado'
    }
    palabras_no_concepto = {
        "desarrollo", "semana", "proceso", "unidad", "etapa", "día",
        "generalidades", "introducción", "serie", "series", "forward", "fourier",
        "tema", "concepto", "parte", "presentación", "fundamentos", "aspectos"
    }

    palabras = texto.split()
    palabras_filtradas = [
        palabra for palabra in palabras
        if len(palabra) > 3 and palabra not in stop_words
    ]

    conceptos = []
    for i in range(len(palabras_filtradas) - 1):
        bigrama = f"{palabras_filtradas[i]} {palabras_filtradas[i+1]}"
        if palabras_filtradas[i] != palabras_filtradas[i+1] and not any(w in palabras_no_concepto for w in bigrama.split()):
            conceptos.append(bigrama)

    for i in range(len(palabras_filtradas) - 2):
        trigrama = f"{palabras_filtradas[i]} {palabras_filtradas[i+1]} {palabras_filtradas[i+2]}"
        if len(set([palabras_filtradas[i], palabras_filtradas[i+1], palabras_filtradas[i+2]])) > 1 and not any(w in palabras_no_concepto for w in trigrama.split()):
            conceptos.append(trigrama)

    conceptos.extend([
        palabra for palabra in palabras_filtradas 
        if palabra not in palabras_no_concepto
    ])
    contador = Counter(conceptos)
    conceptos_principales = [concepto for concepto, freq in contador.most_common(5)]

    if not conceptos_principales:
        conceptos_principales = [
            palabra for palabra in palabras_filtradas 
            if palabra not in palabras_no_concepto
        ][:3]

    return conceptos_principales

def distribuir_unidades_10(unidades):
    U = len(unidades)
    if U < 1 or U > 20:
        raise ValueError("U debe estar entre 1 y 20")
    sesiones_totales = 10

    if U >= sesiones_totales:
        unidades_base_por_sesion = U // sesiones_totales
        sesiones_con_unidad_extra = U % sesiones_totales
        distribucion = []
        idx = 0
        for i in range(sesiones_totales):
            n_unidades = unidades_base_por_sesion + (1 if i < sesiones_con_unidad_extra else 0)
            distribucion.append(unidades[idx:idx + n_unidades])
            idx += n_unidades
        return distribucion
    else:
        unidades_ord = unidades
        sesiones_por_unidad = [1 for _ in range(U)]
        extra = sesiones_totales - U
        for i in range(extra):
            sesiones_por_unidad[i % U] += 1
        distribucion = []
        for idx_u, rep in enumerate(sesiones_por_unidad):
            unidad = unidades_ord[idx_u]
            n_lineas = len(unidad["lineas"])
            partes = []
            if rep == 1:
                partes = [unidad]
            else:
                base = n_lineas // rep
                resto = n_lineas % rep
                ini = 0
                for j in range(rep):
                    fin = ini + base + (1 if j < resto else 0)
                    parte_lineas = unidad["lineas"][ini:fin]
                    parte = {
                        "titulo": f"{unidad['titulo']} (parte {j+1})",
                        "lineas": parte_lineas,
                        "n_lineas": len(parte_lineas),
                        "idx": unidad.get("idx", idx_u)
                    }
                    partes.append(parte)
                    ini = fin
            distribucion.extend([[p] for p in partes])
        return distribucion[:sesiones_totales]

def genera_dict_unidades(data):
    unidades = []
    for i, (titulo, contenidos) in enumerate(data):
        if not isinstance(contenidos, str):
            contenidos = str(contenidos)
        lineas = [fr.strip() for fr in re.split(r'\.\s*|\n', contenidos) if fr.strip()]
        unidades.append({"titulo": titulo, "lineas": lineas, "n_lineas": len(lineas), "idx": i})
    return unidades

def generar_texto_salida(fecha_inicio, fecha_fin, dia_clase, fechas_prueba,
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
    .stFileUploader label {
        color: #2c3e50;
        font-weight: bold;
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

st.header("1. Parámetros Generales")
cols_general = st.columns(3)

with cols_general[0]:
    fecha_inicio = st.date_input("Fecha inicio de clases:", value=date.today(), format="DD/MM/YYYY")
with cols_general[1]:
    fecha_fin = st.date_input("Fecha fin de clases:", value=date.today() + timedelta(weeks=18), format="DD/MM/YYYY")
with cols_general[2]:
    dia_clase = st.selectbox("Día de la semana:", options=list(dias_semana.keys()), index=0)

st.header("2. Feriados y Fechas Especiales")
col_feriado_input, col_feriado_btn = st.columns([0.7, 0.3])

with col_feriado_input:
    feriado_date = st.date_input("Agregar feriados:", value=date.today(), key="add_feriado_date", format="DD/MM/YYYY")
with col_feriado_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Agregar feriado", key="add_feriado_btn"):
        if feriado_date not in st.session_state.feriados_list:
            st.session_state.feriados_list.append(feriado_date)
            st.session_state.feriados_list.sort()
            st.success(f"Feriado '{feriado_date.strftime('%d/%m/%Y')}' agregado.")
        else:
            st.warning("Ese feriado ya fue agregado.")

if st.session_state.feriados_list:
    st.subheader("Feriados agregados:")
    feriado_to_remove = st.selectbox(
        "Seleccione un feriado para quitar:",
        options=[f.strftime('%d/%m/%Y') for f in st.session_state.feriados_list],
        key="remove_feriado_select"
    )
    if st.button("➖ Quitar feriado seleccionado", key="remove_feriado_btn", help="Quita el feriado seleccionado de la lista."):
        if feriado_to_remove:
            date_obj_to_remove = datetime.strptime(feriado_to_remove, '%d/%m/%Y').date()
            if date_obj_to_remove in st.session_state.feriados_list:
                st.session_state.feriados_list.remove(date_obj_to_remove)
                st.success(f"Feriado '{feriado_to_remove}' quitado.")
            else:
                st.error("Error al quitar el feriado.")
        else:
            st.warning("Por favor, seleccione un feriado para quitar.")
    st.write(f"Lista de Feriados: {', '.join([f.strftime('%d/%m/%Y') for f in st.session_state.feriados_list])}")
else:
    st.info("No hay feriados agregados aún.")

st.subheader("Fechas de Pruebas")
cols_pruebas = st.columns(3)
with cols_pruebas[0]:
    prueba1_date = st.date_input("Fecha Prueba 1:", value=date.today() + timedelta(weeks=6), format="DD/MM/YYYY")
with cols_pruebas[1]:
    prueba2_date = st.date_input("Fecha Prueba 2:", value=date.today() + timedelta(weeks=12), format="DD/MM/YYYY")
with cols_pruebas[2]:
    examen_final_date = st.date_input("Fecha Examen Final:", value=date.today() + timedelta(weeks=17), format="DD/MM/YYYY")

# --- AYUDA PEDAGÓGICA (Expander/alerta compatible con cualquier versión) ---
if "show_ayuda" not in st.session_state:
    st.session_state.show_ayuda = True

if st.session_state.show_ayuda:
    with st.expander("🛈 Ayuda para redactar contenidos de unidades pedagógicas", expanded=True):
        st.markdown("""
> **IMPORTANTE:**  
> Para asegurar una planificación clara y efectiva, redacte los contenidos de cada unidad siguiendo estas recomendaciones:
>
> - **Sea claro y preciso:** Escriba cada contenido de forma concreta y sin ambigüedades.
> - **Evite títulos o frases genéricas:** No use palabras como “Generalidades”, “Introducción”, “Unidad 1”, etc. Priorice conceptos específicos y técnicos.
> - **Un concepto por línea:** Organice cada proceso, tema o idea en líneas independientes para facilitar el análisis y la extracción.
> - **Utilice términos técnicos y propios del área:** Ejemplo: “Blastulación”, “Segmentación celular”, “Implantación endometrial”.
> - **Contextualice los contenidos** según el nivel y las necesidades de los estudiantes.
> - **No repita palabras o conceptos innecesariamente.**  
> - **Priorice los contenidos relevantes y útiles para el aprendizaje.**
>
> **Ejemplo correcto:**
> ```
> Ovulación.
> Fecundación.
> Segmentación.
> Blastulación.
> Implantación.
> ```
>
> **Ejemplo incorrecto:**
> ```
> Generalidades.
> Introducción.
> Unidad 1.
> Semana de desarrollo.
> ```
""")
        if st.button("Cerrar ayuda"):
            st.session_state.show_ayuda = False

st.header("3. Unidades Académicas")
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

st.header("4. Plantillas Word (.docx)")
col_plan_upload, col_cron_upload = st.columns(2)

with col_plan_upload:
    uploaded_plan_template = st.file_uploader(
        "Cargar Plantilla de Planeamiento (.docx):",
        type=["docx"],
        key="plan_template_uploader"
    )
    if uploaded_plan_template is not None:
        st.session_state.plantilla_planeamiento_bytes = uploaded_plan_template.read()
        st.info(f"Archivo cargado: {uploaded_plan_template.name}")
    elif st.session_state.plantilla_planeamiento_bytes is None:
         st.info("Ningún archivo de planeamiento seleccionado.")

with col_cron_upload:
    uploaded_cron_template = st.file_uploader(
        "Cargar Plantilla de Cronograma (.docx):",
        type=["docx"],
        key="cron_template_uploader"
    )
    if uploaded_cron_template is not None:
        st.session_state.plantilla_cronograma_bytes = uploaded_cron_template.read()
        st.info(f"Archivo cargado: {uploaded_cron_template.name}")
    elif st.session_state.plantilla_cronograma_bytes is None:
        st.info("Ningún archivo de cronograma seleccionado.")

st.markdown("<br>", unsafe_allow_html=True) # Espaciador
if st.button("🚀 Generar Planificación", key="generate_plan_btn"):
    unidades_input = []
    for unit_data in st.session_state.unidades_data:
        title = unit_data['title'].strip()
        contents = unit_data['content'].strip()
        if title and contents:
            unidades_input.append((title, contents))

    if not unidades_input:
        st.error("Debe ingresar al menos una unidad con título y contenido.")
    else:
        with st.spinner("Generando planificación..."):
            try:
                fechas_prueba = [prueba1_date, prueba2_date]
                examen_final = examen_final_date
                unidades = genera_dict_unidades(unidades_input)
                total_sesiones = 17
                dia_clase_num = dias_semana[dia_clase]
                # ----- MODIFICACIÓN: No omitir feriados -----
                fechas_sesiones = []
                f = fecha_inicio
                while len(fechas_sesiones) < total_sesiones:
                    if f.weekday() == dia_clase_num:
                        fechas_sesiones.append(f)
                        f += timedelta(days=7)
                    else:
                        f += timedelta(days=1)
                # --------------------------------------------
                for i, pr in enumerate(fechas_prueba):
                    if pr not in fechas_sesiones:
                        st.warning(f"La fecha de Prueba {i+1} ({pr.strftime('%d/%m/%Y')}) no es un día de clase válido o coincide con un feriado.")
                if examen_final not in fechas_sesiones:
                    st.warning(f"La fecha del Examen Final ({examen_final.strftime('%d/%m/%Y')}) no es un día de clase válido o coincide con un feriado.")

                sesiones = ["Clase normal"] * total_sesiones
                idx_prueba = []
                for pr in fechas_prueba:
                    if pr in fechas_sesiones:
                        idx_prueba.append(fechas_sesiones.index(pr))
                if fechas_sesiones[-1] == examen_final:
                    sesiones[-1] = "Examen final"
                else:
                    st.warning(f"La fecha de examen final ({examen_final.strftime('%d/%m/%Y')}) no corresponde a la última sesión calculada ({fechas_sesiones[-1].strftime('%d/%m/%Y')}). La última sesión se marcará como Examen Final.")
                    sesiones[-1] = "Examen final"
                for i, idx in enumerate(idx_prueba):
                    if 0 <= idx < total_sesiones:
                        if idx > 0 and sesiones[idx-1] == "Clase normal":
                            sesiones[idx-1] = "Retroalimentación"
                        sesiones[idx] = "Prueba parcial"
                        if idx < len(sesiones) - 1 and sesiones[idx+1] == "Clase normal":
                            sesiones[idx+1] = "Revisión de prueba"
                sesiones_unidades = distribuir_unidades_10(unidades)
                fragmentos_sesiones = []
                niveles = list(verbos_bloom.keys())
                nivel_idx = 0

                for lista_unidades in sesiones_unidades:
                    contenido_total = []
                    titulos = []
                    for unidad in lista_unidades:
                        titulos.append(unidad["titulo"])
                        contenido_total.extend(unidad["lineas"])
                    fragmento = " ".join(contenido_total)
                    conceptos = extraer_conceptos_simple(fragmento)
                    concepto = ", ".join(conceptos) if conceptos else fragmento[:50] + "..."
                    nivel = niveles[nivel_idx % len(niveles)]
                    verbo = random.choice(verbos_bloom[nivel])
                    actividad = plantillas_actividades[nivel].format(concepto)
                    fragmentos_sesiones.append({
                        "Unidad": " / ".join(titulos),
                        "Contenido": fragmento,
                        "Concepto": concepto,
                        "Nivel": nivel,
                        "Verbo": verbo,
                        "Actividad": actividad,
                        "Recursos": ", ".join(recursos_bloom[nivel]),
                        "Evaluacion": ", ".join(evaluacion_bloom[nivel])
                    })
                    nivel_idx += 1

                lista_sesiones_word = []
                idx_normal = 0

                for idx, (tipo, fecha) in enumerate(zip(sesiones, fechas_sesiones)):
                    sesion_dict = {
                        "Numero": idx+1,
                        "Fecha": fecha.strftime("%d/%m/%Y"),
                        "Evento": tipo,
                        "En_feriado": fecha in st.session_state.feriados_list,
                        "Planificacion": None
                    }
                    if tipo == "Clase normal":
                        if idx_normal < len(fragmentos_sesiones):
                            p = fragmentos_sesiones[idx_normal]
                            sesion_dict["Planificacion"] = {
                                "Unidad": p["Unidad"],
                                "Contenido": p["Contenido"],
                                "Verbo": p["Verbo"],
                                "Concepto": p["Concepto"],
                                "Nivel": p["Nivel"],
                                "Actividad": p["Actividad"],
                                "Recursos": p["Recursos"],
                                "Evaluacion": p["Evaluacion"],
                                "Retroalimentacion": random.choice(retro),
                                "Introduccion": random.choice(intro),
                                "Inicio": random.choice(inicio),
                                "Desarrollo": random.choice(desarrollo),
                                "Cierre": random.choice(cierre)
                            }
                        else:
                            sesion_dict["Planificacion"] = {
                                "Unidad": "Sin unidad asignada", "Contenido": "Sin contenido asignado",
                                "Verbo": "N/A", "Concepto": "N/A", "Nivel": "N/A", "Actividad": "N/A",
                                "Recursos": "N/A", "Evaluacion": "N/A", "Retroalimentacion": "N/A",
                                "Introduccion": "N/A", "Inicio": "N/A", "Desarrollo": "N/A", "Cierre": "N/A"
                            }
                        idx_normal += 1
                    else:
                        sesion_dict["Planificacion"] = {
                            "Unidad": "", "Contenido": "", "Verbo": "", "Concepto": "",
                            "Nivel": "", "Actividad": "", "Recursos": "", "Evaluacion": "",
                            "Retroalimentacion": "", "Introduccion": "", "Inicio": "", "Desarrollo": "", "Cierre": ""
                        }

                    lista_sesiones_word.append(sesion_dict)

                context = {
                    "PERIODO": f"{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}",
                    "DIA_CLASE": dia_clase.capitalize(),
                    "FERIADOS": ', '.join([f.strftime('%d/%m/%Y') for f in st.session_state.feriados_list]) if st.session_state.feriados_list else "Ninguno",
                    "PRUEBAS": ', '.join([f.strftime('%d/%m/%Y') for f in fechas_prueba if f in fechas_sesiones]),
                    "EXAMEN_FINAL": fechas_sesiones[-1].strftime('%d/%m/%Y'),
                    "UNIDADES": [u["titulo"] for u in unidades],
                }

                for sesion in lista_sesiones_word:
                    pref = f"SESION_{sesion['Numero']}_"
                    context[pref + "FECHA"] = sesion['Fecha']
                    context[pref + "EVENTO"] = sesion['Evento']
                    context[pref + "ADVERTENCIA"] = "⚠️ ¡Advertencia! Esta sesión coincide con un feriado." if sesion["En_feriado"] else ""
                    planif = sesion.get("Planificacion")
                    if planif:
                        context[pref + "UNIDAD"] = f" UNIDAD : {planif['Unidad']}" if planif['Unidad'] else ""
                        context[pref + "CONTENIDO"] = f" CONTENIDO: {planif['Contenido']}" if planif['Contenido'] else ""
                        context[pref + "OBJETIVO"] = f" OBJETIVO: El estudiante será capaz de {planif['Verbo']} {planif['Concepto']}" if planif['Verbo'] and planif['Concepto'] else ""
                        context[pref + "NIVEL_BLOOM"] = f"Nivel Bloom: {planif['Nivel']}" if planif['Nivel'] else ""
                        context[pref + "RETROALIMENTACION"] = f"Retroalimentación: {planif['Retroalimentacion']}" if planif['Retroalimentacion'] else ""
                        context[pref + "INTRODUCCION"] = f"Introducción: {planif['Introduccion']}" if planif['Introduccion'] else ""
                        context[pref + "INICIO"] = f"Inicio: {planif['Inicio']}" if planif['Inicio'] else ""
                        context[pref + "DESARROLLO"] = f"Desarrollo: {planif['Desarrollo']}" if planif['Desarrollo'] else ""
                        context[pref + "CIERRE"] = f"Cierre: {planif['Cierre']}" if planif['Cierre'] else ""
                        if sesion["Evento"] == "Clase normal":
                            context[pref + "ESTRATEGIAS"] = f"Estrategias de aprendizaje: {planif['Actividad']}"
                            context[pref + "RECURSOS"] = f"Recursos: {planif['Recursos']}"
                            context[pref + "EVALUACION"] = f"Evaluación: {planif['Evaluacion']}"
                        else:
                            context[pref + "ESTRATEGIAS"] = ""
                            context[pref + "RECURSOS"] = ""
                            context[pref + "EVALUACION"] = ""
                    else:
                        campos_with_prefix = [
                            "UNIDAD", "CONTENIDO", "OBJETIVO", "NIVEL_BLOOM", "ESTRATEGIAS",
                            "RETROALIMENTACION", "INTRODUCCION", "INICIO", "DESARROLLO",
                            "CIERRE", "RECURSOS", "EVALUACION"
                        ]
                        for campo in campos_with_prefix:
                            context[pref + campo] = ""

                out = generar_texto_salida(fecha_inicio, fecha_fin, dia_clase, fechas_prueba,
                                           fechas_sesiones, unidades, lista_sesiones_word, st.session_state.feriados_list)
                st.session_state.generated_context = context
                st.session_state.generated_out_text = out
                st.success("¡Planificación generada exitosamente! Consulte los resultados a continuación.")

            except Exception as e:
                st.error(f"Error al generar la planificación: {str(e)}")

st.header("5. Resultados")

if st.session_state.generated_out_text:
    st.subheader("Resumen de la Planificación")
    st.text_area(
        "Planificación Detallada:",
        value=st.session_state.generated_out_text,
        height=400,
        disabled=True,
        key="results_text_area"
    )

    st.subheader("Descargar Documentos")
    col_download_plan, col_download_cron, col_download_txt = st.columns(3)

    with col_download_plan:
        if st.session_state.plantilla_planeamiento_bytes and st.session_state.generated_context:
            try:
                doc_planeamiento = DocxTemplate(io.BytesIO(st.session_state.plantilla_planeamiento_bytes))
                doc_planeamiento.render(st.session_state.generated_context)
                bio = io.BytesIO()
                doc_planeamiento.save(bio)
                bio.seek(0)
                st.download_button(
                    label="Descargar Planeamiento Word",
                    data=bio,
                    file_name="Planeamiento_Semestral.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_plan_btn"
                )
            except Exception as e:
                st.error(f"Error al preparar el documento de planeamiento: {str(e)}")
        else:
            st.warning("Cargue una plantilla de planeamiento para descargar.")

    with col_download_cron:
        if st.session_state.plantilla_cronograma_bytes and st.session_state.generated_context:
            try:
                doc_cronograma = DocxTemplate(io.BytesIO(st.session_state.plantilla_cronograma_bytes))
                doc_cronograma.render(st.session_state.generated_context)
                bio = io.BytesIO()
                doc_cronograma.save(bio)
                bio.seek(0)
                st.download_button(
                    label="Descargar Cronograma Word",
                    data=bio,
                    file_name="Cronograma_Semestral.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_cron_btn"
                )
            except Exception as e:
                st.error(f"Error al preparar el documento de cronograma: {str(e)}")
        else:
            st.warning("Cargue una plantilla de cronograma para descargar.")

    with col_download_txt:
        st.download_button(
            label="Descargar Resumen TXT",
            data=st.session_state.generated_out_text.encode('utf-8'),
            file_name="Resumen_Planeamiento.txt",
            mime="text/plain",
            key="download_txt_btn"
        )
else:
    st.info("Presione '🚀 Generar Planificación' para ver los resultados y habilitar las descargas.")
