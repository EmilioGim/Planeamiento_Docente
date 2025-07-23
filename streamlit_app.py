import streamlit as st
import random
import re
from datetime import datetime, timedelta, date
from io import BytesIO
import nltk

# Función para descargar recursos NLTK solo si no están disponibles, exige internet en el entorno
def download_nltk_resources():
    recursos = ['punkt', 'averaged_perceptron_tagger', 'wordnet']
    for recurso in recursos:
        try:
            if recurso == 'punkt':
                nltk.data.find('tokenizers/punkt')
            elif recurso == 'averaged_perceptron_tagger':
                nltk.data.find('taggers/averaged_perceptron_tagger')
            else:
                nltk.data.find(f'corpora/{recurso}')
        except LookupError:
            nltk.download(recurso)

download_nltk_resources()

from textblob import TextBlob

from docxtpl import DocxTemplate
from docx import Document

# Diccionarios Bloom y plantillas

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

dias_semana = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5
}

def extraer_conceptos_textblob(texto):
    blob = TextBlob(texto)
    conceptos = list(blob.noun_phrases)
    return conceptos

def extraer_texto_docx(archivo_docx):
    doc = Document(archivo_docx)
    full_text = []
    for para in doc.paragraphs:
        txt = para.text.strip()
        if txt:
            full_text.append(txt)
    return "\n".join(full_text)

def extraer_unidades_plan(plan_texto):
    unidades = []
    lineas = plan_texto.split('\n')
    titulo_actual = None
    contenido_actual = []
    for linea in lineas:
        if re.match(r'^Unidad\s+\w+', linea, re.I):
            if titulo_actual is not None:
                unidades.append((titulo_actual, "\n".join(contenido_actual)))
            contenido_actual = []
            titulo_actual = linea.strip()
        else:
            if titulo_actual is not None:
                contenido_actual.append(linea.strip())
    if titulo_actual is not None:
        unidades.append((titulo_actual, "\n".join(contenido_actual)))
    return unidades

def genera_dict_unidades(data):
    unidades = []
    for i, (titulo, contenidos) in enumerate(data):
        lineas = [fr.strip() for fr in re.split(r'\.\s*|\n', contenidos) if fr.strip()]
        unidades.append({"titulo": titulo, "lineas": lineas, "n_lineas": len(lineas), "idx": i})
    return unidades

def distribuir_unidades_10_ordenado(unidades):
    \"\"\"Distribuye las unidades en 10 sesiones manteniendo el orden original.\"\"\"
    U = len(unidades)
    sesiones = 10
    distribucion = []
    if U >= sesiones:
        idx = 0
        for i in range(sesiones):
            if idx < U:
                distribucion.append([unidades[idx]])
                idx += 1
            else:
                distribucion.append([])
        return distribucion
    else:
        sesiones_por_unidad = [1 for _ in range(U)]
        extra = sesiones - U
        for i in range(extra):
            sesiones_por_unidad[i % U] += 1
        distribucion = []
        for idx_u, rep in enumerate(sesiones_por_unidad):
            unidad = unidades[idx_u]
            n_lineas = len(unidad["lineas"])
            if rep == 1:
                distribucion.append([unidad])
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
                    distribucion.append([parte])
                    ini = fin
        return distribucion[:10]

def main():
    st.set_page_config(page_title="Planeamiento Semestral", layout="wide")
    st.title("Planeamiento docente semestral")

    st.markdown("### Paso 1: Ingrese datos del docente")
    
    nombre_docente = st.text_input("Nombre del docente")
    curso = st.text_input("Curso o asignatura")
    semestre = st.selectbox("Semestre", ["1", "2", "3", "4", "5", "6"])

    st.markdown("---")
    st.markdown("### Paso 2: Suba el archivo Word con las unidades y contenidos académicos")
    archivo_plan = st.file_uploader("Seleccione archivo Word (.docx)", type=["docx"])
    
    if archivo_plan is not None:
        texto_plan = extraer_texto_docx(archivo_plan)
        st.text_area("Vista previa del plan", texto_plan, height=300)

        unidades_texto = extraer_unidades_plan(texto_plan)
        unidades = genera_dict_unidades(unidades_texto)

        distribucion_sesiones = distribuir_unidades_10_ordenado(unidades)

        st.markdown("### Paso 3: Generar planeamiento docente")

        # Aquí podrías generar un planeamiento con el contenido cargado y mostrarlo

        if st.button("Generar planeamiento (simulado)"):
            # Ejemplo: muestra títulos de sesiones generados
            for i, sesion in enumerate(distribucion_sesiones):
                st.write(f"Sesión {i+1}:")
                for unidad in sesion:
                    st.write(f"- {unidad['titulo']} ({unidad['n_lineas']} líneas)")

        st.markdown("---")
        
        st.markdown("### Paso 4: Suba las dos plantillas Word para generar el cronograma y planeamiento")

        plantilla1 = st.file_uploader("Plantilla Cronograma (Word)", type=["docx"], key="plantilla1")
        plantilla2 = st.file_uploader("Plantilla Planeamiento (Word)", type=["docx"], key="plantilla2")

        if plantilla1 and plantilla2:
            st.success("Plantillas cargadas correctamente. Aquí iría la generación de archivos y descarga.")

            # Aquí deberías usar docxtpl para rellenar las plantillas y luego ofrecer descarga
            # Ejemplo muy básico para descarga:
            @st.cache_data
            def generar_docx_placeholder():
                # Aquí deberías generar el documento con docxtpl y devolver bytes
                return b"Contenido del archivo Word generado"

            contenido_generado = generar_docx_placeholder()
            st.download_button("Descargar documento generado", data=contenido_generado, file_name="planeamiento_generado.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

if __name__ == "__main__":
    main()
