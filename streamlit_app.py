import streamlit as st
from datetime import date, timedelta
import random
import re
import io
from docx import Document # Para el segundo archivo Word
from docxtpl import DocxTemplate # Para el primer archivo Word (plantilla)

# Asegúrate de que los imports de docx y docxtpl estén aquí
# y que 'python-docx' esté en tu requirements.txt

# ============ CONFIGURACIÓN DE SEGURIDAD ============
CORRECT_PASSWORD = "#Emilio#Planeamiento#" # ¡CAMBIA ESTO POR UNA CONTRASEÑA REAL!

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'planificacion' not in st.session_state:
    st.session_state.planificacion = None
if 'plan_creada' not in st.session_state:
    st.session_state.plan_creada = False
if 'contexto_docx' not in st.session_state:
    st.session_state.contexto_docx = None

# ============ PÁGINA DE AUTENTICACIÓN ============
if not st.session_state.authenticated:
    st.title("Bienvenido al Planificador Académico")
    st.write("Por favor, ingresa la contraseña para acceder.")
    password_input = st.text_input("Contraseña:", type="password")

    if st.button("Acceder"):
        if password_input == CORRECT_PASSWORD:
            st.session_state.authenticated = True
            st.success("Acceso concedido. ¡Bienvenido!")
            st.rerun() # Recargar la página para mostrar la aplicación completa
        else:
            st.error("Contraseña incorrecta. Por favor, inténtalo de nuevo.")
            st.write("Si no tienes la contraseña, contacta al administrador.")
    st.stop() # Detiene la ejecución si no está autenticado

# ============ CÓDIGO DE LA APLICACIÓN PRINCIPAL (SOLO SI AUTENTICADO) ============

# ============ BLOOM Y PLANTILLAS (DEFINIDOS GLOBALMENTE) =============
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


st.title("Planificador semanal académico interactivo")

# 1. Subida de plantilla: debe hacerse primero (o antes de generar)
plantilla_archivo = st.file_uploader(
    "Sube tu plantilla .docx para el reporte final (opcional, hazlo antes de 'Generar planificación')",
    type="docx"
)

# ========== Ingreso de datos interactivos ============
st.header("Configuración de Unidades")
n = st.number_input("¿Cuántas unidades desea ingresar?", 1, 10, 1, 1)
unidades = {}

for i in range(int(n)):
    with st.expander(f"Unidad {i+1}"):
        titulo = st.text_input(f"Título de la Unidad {i+1}:", key=f"titulo_{i}")
        contenido = st.text_area(
            f"Contenido (cada frase en una línea) para Unidad {i+1}:",
            key=f"contenido_{i}"
        )
        if titulo and contenido:
            unidades[titulo] = [line.strip() for line in contenido.splitlines() if line.strip()]

st.header("Fechas y eventos del calendario")
fecha_inicio = st.date_input("Fecha de inicio del semestre:", value=date.today())
fecha_fin = st.date_input("Fecha de fin del semestre:", value=date.today()+timedelta(weeks=16))
dia_clase = st.selectbox("Día de clase:", ["lunes", "martes", "miércoles", "jueves", "viernes"])

st.subheader("Feriados y Eventos Especiales")
n_feriados = st.number_input("Cantidad de feriados:", 0, 10, 0, 1)
feriados = []
for j in range(int(n_feriados)):
    feriados.append(st.date_input(f"Feriado #{j+1}:", key=f"feriado_{j}"))

st.subheader("Fechas de Pruebas Parciales")
fecha_prueba_1 = st.date_input("Fecha de prueba parcial 1:")
fecha_prueba_2 = st.date_input("Fecha de prueba parcial 2:")

fecha_final = st.date_input("Fecha de examen final:")

# ============ Botón para generar planificación ===============
if st.button("Generar planificación"):
    total_sesiones_normales = 10
    n_unidades = len(unidades)
    sesiones_por_unidad = [total_sesiones_normales // n_unidades] * n_unidades if n_unidades else []
    for i in range(total_sesiones_normales % n_unidades if n_unidades else 0):
        sesiones_por_unidad[i] += 1

    # Procesamiento spaCy (opcional)
   try:
       import spacy
       try:
           nlp = spacy.load("es_core_news_sm")
       except OSError:
           from spacy.cli import download
           download("es_core_news_sm")
           nlp = spacy.load("es_core_news_sm")
    except Exception as e:
        st.warning("spaCy no está instalado (solo usará 'el contenido' como concepto): " + str(e))
        nlp = None




    fragmentos_sesiones = []
    niveles = list(verbos_bloom.keys())
    nivel_idx = 0

    for idx, (unidad, frases) in enumerate(unidades.items()):
        cantidad = sesiones_por_unidad[idx]
        por_sesion = max(1, len(frases) // cantidad)
        for s in range(cantidad):
            fragmento = " ".join(frases[s*por_sesion:(s+1)*por_sesion])
            if nlp:
                doc = nlp(fragmento.lower())
                conceptos = [chunk.text for chunk in doc.noun_chunks if len(chunk.text) > 2]
                concepto = conceptos[0] if conceptos else "el contenido"
            else:
                concepto = "el contenido"
            nivel = niveles[nivel_idx % len(niveles)]
            verbo = random.choice(verbos_bloom[nivel])
            actividad = plantillas_actividades[nivel].format(concepto)
            fragmentos_sesiones.append({
                "Unidad": unidad,
                "Contenido": fragmento,
                "Concepto": concepto,
                "Nivel": nivel,
                "Verbo": verbo,
                "Actividad": actividad,
                "Nivel_idx": nivel_idx
            })
            nivel_idx += 1

    dias_semana = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4}
    dia_clase_num = dias_semana.get(dia_clase, 0)
    pruebas = []
    fechas_pruebas = [fecha_prueba_1, fecha_prueba_2]
    try:
        fecha_inicio_dt = fecha_inicio
        for f_prueba in fechas_pruebas:
            fecha_prueba_dt = f_prueba
            dia_inicio_semana = fecha_inicio_dt.weekday()
            ajuste_dia = (dia_clase_num - dia_inicio_semana) % 7
            primer_dia_clase = fecha_inicio_dt + timedelta(days=ajuste_dia)
            if fecha_prueba_dt < primer_dia_clase:
                sesion_prueba = 1
            else:
                semanas = ((fecha_prueba_dt - primer_dia_clase).days // 7) + 1
                sesion_prueba = semanas
            pruebas.append(sesion_prueba)
    except Exception as e:
        pruebas = [8, 13] # Valores por defecto si falla el cálculo
    retro_sesiones = [p - 1 for p in pruebas if p > 1]
    revision_sesiones = [p + 1 for p in pruebas]

    def generar_planificacion():
        plan = []
        sesion_num = 1
        while sesion_num <= 17:
            if sesion_num == 17:
                dia_evento = fecha_final
                estado = "Examen final"
                en_feriado = dia_evento in feriados
            else:
                fecha_base = fecha_inicio + timedelta(weeks=sesion_num - 1)
                dia_evento = fecha_base + timedelta(days=(dia_clase_num - fecha_base.weekday()) % 7)
                en_feriado = dia_evento in feriados
                if sesion_num in pruebas:
                    estado = "Prueba parcial"
                elif sesion_num in retro_sesiones:
                    estado = "Retroalimentación"
                elif sesion_num in revision_sesiones:
                    estado = "Revisión de prueba"
                else:
                    estado = "Clase normal"
            plan.append({
                "Sesion": sesion_num,
                "Fecha": dia_evento,
                "Evento": estado,
                "En_feriado": en_feriado
            })
            sesion_num += 1
        return plan

    plan_semanal = generar_planificacion()

    sesiones_normales_idx = [i for i, s in enumerate(plan_semanal) if s["Evento"] == "Clase normal"]
    if len(sesiones_normales_idx) < total_sesiones_normales:
        st.warning("Hay menos sesiones normales de las requeridas para clases normales. Verifica fechas de feriados y eventos.")
        total_asignar = len(sesiones_normales_idx)
    else:
        total_asignar = total_sesiones_normales

    for idx, frag_idx in enumerate(range(total_asignar)):
        i = sesiones_normales_idx[idx]
        plan_semanal[i]["Planificacion"] = fragmentos_sesiones[frag_idx]

    # Guardamos en el estado
    st.session_state.planificacion = plan_semanal
    st.session_state.plan_creada = True

    # Guardar contexto para el docx en estado
    contexto_docx = {}
    for sesion in plan_semanal:
        num = sesion["Sesion"]
        pref = f"SESION_{num}_"
        contexto_docx[pref + "FECHA"] = sesion["Fecha"].strftime("%Y-%m-%d")
        contexto_docx[pref + "EVENTO"] = sesion["Evento"]
        if sesion["Evento"] == "Clase normal" and "Planificacion" in sesion:
            p = sesion["Planificacion"]
            contexto_docx[pref + "UNIDAD"] = p["Unidad"]
            contexto_docx[pref + "CONTENIDO"] = p["Contenido"]
            contexto_docx[pref + "OBJETIVO"] = f"El estudiante será capaz de {p['Verbo']} {p['Concepto']}"
            contexto_docx[pref + "NIVEL_BLOOM"] = p["Nivel"]
            contexto_docx[pref + "RETROALIMENTACION"] = random.choice(retro)
            contexto_docx[pref + "INTRODUCCION"] = random.choice(intro)
            contexto_docx[pref + "INICIO"] = random.choice(inicio)
            contexto_docx[pref + "DESARROLLO"] = p["Actividad"]
            contexto_docx[pref + "CIERRE"] = random.choice(cierre)
            contexto_docx[pref + "RECURSOS"] = ", ".join(recursos_bloom[p["Nivel"]])
            contexto_docx[pref + "EVALUACION"] = ", ".join(evaluacion_bloom[p["Nivel"]])
        else:
            contexto_docx[pref + "UNIDAD"] = ""
            contexto_docx[pref + "CONTENIDO"] = ""
            contexto_docx[pref + "OBJETIVO"] = ""
            contexto_docx[pref + "NIVEL_BLOOM"] = ""
            contexto_docx[pref + "RETROALIMENTACION"] = ""
            contexto_docx[pref + "INTRODUCCION"] = ""
            contexto_docx[pref + "INICIO"] = ""
            contexto_docx[pref + "DESARROLLO"] = ""
            contexto_docx[pref + "CIERRE"] = ""
            contexto_docx[pref + "RECURSOS"] = ""
            contexto_docx[pref + "EVALUACION"] = ""
            contexto_docx[pref + "ADVERTENCIA"] = "⚠️ Coincide con feriado." if sesion["En_feriado"] else ""
    st.session_state.contexto_docx = contexto_docx

# ============= Mostrar planificación y botones de descarga (si disponible) ==============

if st.session_state.get("plan_creada", False):
    st.header("📋 Planificación semanal generada")
    plan_semanal = st.session_state.planificacion
    for sesion in plan_semanal:
        st.markdown(f"**Sesión {sesion['Sesion']:2d} | {sesion['Fecha']} | {sesion['Evento']}**")
        if sesion["Evento"] == "Clase normal" and "Planificacion" in sesion:
            p = sesion["Planificacion"]
            st.markdown(
                f"- Unidad: {p['Unidad']}\n"
                f"- Contenido: {p['Contenido']}\n"
                f"- Objetivo: El estudiante será capaz de {p['Verbo']} {p['Concepto']}\n"
                f"- Nivel Bloom: {p['Nivel']}\n"
                f"- Momentos Didácticos: Retroalimentación ({random.choice(retro)}), "
                f"Introducción ({random.choice(intro)}), "
                f"Inicio ({random.choice(inicio)}), "
                f"Desarrollo ({p['Actividad']}), Cierre ({random.choice(cierre)})\n"
                f"- Recursos: {', '.join(recursos_bloom[p['Nivel']])}\n"
                f"- Evaluación: {', '.join(evaluacion_bloom[p['Nivel']])}"
            )
        if sesion["En_feriado"]:
            st.warning("¡Advertencia! Esta sesión coincide con un feriado. Reagendar si es necesario.")

    # ====== SEGUNDO BOTÓN DE DESCARGA: ARCHIVO WORD CON EL RESUMEN VISUAL ========
    st.subheader("Descargar informes")
    doc_resumen = Document()
    doc_resumen.add_heading("Planificación semanal generada", 0)

    for sesion in plan_semanal:
        doc_resumen.add_heading(f"Sesión {sesion['Sesion']} | {sesion['Fecha']} | {sesion['Evento']}", level=1)
        if sesion["Evento"] == "Clase normal" and "Planificacion" in sesion:
            p = sesion["Planificacion"]
            doc_resumen.add_paragraph(f"Unidad: {p['Unidad']}")
            doc_resumen.add_paragraph(f"Contenido: {p['Contenido']}")
            doc_resumen.add_paragraph(f"Objetivo: El estudiante será capaz de {p['Verbo']} {p['Concepto']}")
            doc_resumen.add_paragraph(f"Nivel Bloom: {p['Nivel']}")
            doc_resumen.add_paragraph(
                f"Momentos Didácticos: Retroalimentación ({random.choice(retro)}), "
                f"Introducción ({random.choice(intro)}), Inicio ({random.choice(inicio)}), "
                f"Desarrollo ({p['Actividad']}), Cierre ({random.choice(cierre)})"
            )
            doc_resumen.add_paragraph(f"Recursos: {', '.join(recursos_bloom[p['Nivel']])}")
            doc_resumen.add_paragraph(f"Evaluación: {', '.join(evaluacion_bloom[p['Nivel']])}")
        if sesion["En_feriado"]:
            doc_resumen.add_paragraph("¡Advertencia! Esta sesión coincide con un feriado. Reagendar si es necesario.")
        doc_resumen.add_paragraph("") # Línea en blanco para separar sesiones

    file_resumen = io.BytesIO()
    doc_resumen.save(file_resumen)
    file_resumen.seek(0)
    st.download_button("Descargar Informe-Resumen (Word)", file_resumen.getvalue(), "planificacion_resumen.docx")

    # ====== PRIMER BOTÓN DE DESCARGA: ARCHIVO WORD DESDE PLANTILLA ========
    if plantilla_archivo and st.session_state.contexto_docx:
        try:
            doc = DocxTemplate(plantilla_archivo)
            doc.render(st.session_state.contexto_docx)
            output_word = io.BytesIO()
            doc.save(output_word)
            output_word.seek(0)
            st.download_button("Descargar Planificación (Plantilla Word)", output_word.getvalue(), "planificacion_personalizada.docx")
        except Exception as e:
            st.warning(f"Error al generar el archivo Word desde la plantilla: {e}")
    elif not plantilla_archivo:
        st.info("Para descargar la Planificación personalizada, sube primero la plantilla .docx y luego vuelve a presionar 'Generar planificación'.")
