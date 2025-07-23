import streamlit as st
import random
import re
from datetime import datetime, timedelta, date
from io import BytesIO

from textblob import TextBlob

try:
    from docxtpl import DocxTemplate
except ImportError:
    import subprocess
    subprocess.run(["python", "-m", "pip", "install", "docxtpl"])
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
dias_semana = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4, "sábado": 5}

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
    """
    Distribuye las unidades en 10 sesiones manteniendo el orden original.
    Si hay menos de 10 unidades, divide cada unidad en partes, pero sigue el orden.
    """
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
        # Si hay menos de 10 unidades, divide cada unidad en partes manteniendo el orden.
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
    st.markdown("<h1 style='text-align: center;'>Planeamiento Semestral Bloom + TextBlob</h1>", unsafe_allow_html=True)
    st.info("Complete los datos. Todas las fechas se eligen con el calendario. El examen final SIEMPRE es la sesión 17, aunque esté fuera del período de clases.")

    with st.expander("Parámetros generales", expanded=True):
        col1, col2, col3 = st.columns([1,1,1])
        fecha_inicio = col1.date_input("Fecha inicio de clases", value=date.today())
        fecha_fin = col2.date_input("Fecha fin de clases", value=date.today() + timedelta(weeks=18))
        dia_clase = col3.selectbox("Día de la semana de clase", list(dias_semana.keys()), index=0)

    with st.expander("Feriados y fechas especiales", expanded=True):
        st.write("Seleccione los feriados con el calendario (puede elegir varios).")
        feriados_list = st.multiselect("Feriados", options=[fecha_inicio + timedelta(days=7*i) for i in range(20)], format_func=lambda d: d.strftime("%d/%m/%Y"))
        st.write("Las fechas válidas para pruebas y examen final son los días de clase:")
        total_sesiones = 17
        dia_clase_num = dias_semana[dia_clase]
        fechas_sesiones = []
        f = fecha_inicio
        while len(fechas_sesiones) < total_sesiones:
            if f.weekday() == dia_clase_num:
                fechas_sesiones.append(f)
                f += timedelta(days=7)
            else:
                f += timedelta(days=1)
        st.table([f.strftime("%d/%m/%Y") for f in fechas_sesiones])

        prueba1 = st.date_input("Prueba 1", value=fechas_sesiones[5])
        prueba2 = st.date_input("Prueba 2", value=fechas_sesiones[10])
        examen_final = st.date_input("Examen final (será la sesión 17)", value=fechas_sesiones[-1])

        if prueba1 not in fechas_sesiones:
            st.warning(f"La fecha de Prueba 1 ({prueba1.strftime('%d/%m/%Y')}) no es día de clase. Elija una de la tabla de arriba.")
        if prueba2 not in fechas_sesiones:
            st.warning(f"La fecha de Prueba 2 ({prueba2.strftime('%d/%m/%Y')}) no es día de clase. Elija una de la tabla de arriba.")
        if examen_final != fechas_sesiones[-1]:
            st.warning(f"El examen final se programará para la última sesión: {fechas_sesiones[-1].strftime('%d/%m/%Y')}.")

    st.markdown("---")
    st.markdown("## Unidades académicas")
    st.markdown("### Cargue el archivo Word (.docx) con el Plan de Estudios completo")

    archivo_plan = st.file_uploader("Seleccione el archivo Word con el Plan de Estudios", type=["docx"])

    if archivo_plan is not None:
        texto_plan = extraer_texto_docx(BytesIO(archivo_plan.read()))
        unidades_input = extraer_unidades_plan(texto_plan)
        
        if not unidades_input:
            st.error("No se encontraron unidades con formato esperado (líneas que empiecen con 'Unidad').")
            return
        
        st.success(f"Se detectaron {len(unidades_input)} unidades")
        
        # Muestra resumen de unidades
        for titulo, contenido in unidades_input:
            st.subheader(titulo)
            lineas = [fr.strip() for fr in re.split(r'\.\s*|\n', contenido) if fr.strip()]
            preview = " - ".join(lineas[:3])
            if len(lineas) > 3:
                preview += " ..."
            st.write(preview)
    else:
        st.warning("Por favor, cargue un archivo Word con el Plan de Estudios.")
        return

    st.markdown("---")
    st.markdown("## Plantillas Word (.docx)")
    plantilla_planeamiento = st.file_uploader("Plantilla Planeamiento (.docx)", type=["docx"])
    plantilla_cronograma = st.file_uploader("Plantilla Cronograma (.docx)", type=["docx"])

    st.markdown("---")
    generar = st.button("🚀 Generar planificación", use_container_width=True)
    if generar:
        unidades = genera_dict_unidades(unidades_input)
        clases_normales = 10

        fechas_prueba = []
        for pr, label in zip([prueba1, prueba2], ["Prueba 1", "Prueba 2"]):
            if pr not in fechas_sesiones:
                st.error(f"La fecha de {label} debe ser uno de los días de clase. Ajuste la fecha.")
                return
            else:
                fechas_prueba.append(pr)
        fecha_final_ = fechas_sesiones[-1]

        sesiones = ["Clase normal"] * total_sesiones
        idx_prueba = [fechas_sesiones.index(f) for f in fechas_prueba]
        sesiones[-1] = "Examen final"
        for i, idx in enumerate(idx_prueba):
            sesiones[idx-1] = "Retroalimentación"
            sesiones[idx] = "Prueba parcial"
            sesiones[idx+1] = "Revisión de prueba"

        sesiones_normales_idx = [i for i, tipo in enumerate(sesiones) if tipo == "Clase normal"]
        sesiones_unidades = distribuir_unidades_10_ordenado(unidades)

        fragmentos_sesiones = []
        niveles = list(verbos_bloom.keys())
        nivel_idx = 0
        for lista_unidades in sesiones_unidades:
            contenido_total = []
            titulos = []
            for unidad in lista_unidades:
                titulos.append(unidad["titulo"])
                contenido_total += unidad["lineas"]
            fragmento = " ".join(contenido_total)
            conceptos = extraer_conceptos_textblob(fragmento)
            concepto = ", ".join(conceptos) if conceptos else fragmento.strip()
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

        # Generación de lista de sesiones para visualización y Word
        lista_sesiones_word = []
        idx_normal = 0
        for idx, (tipo, fecha) in enumerate(zip(sesiones, fechas_sesiones)):
            sesion_dict = {
                "Numero": idx+1,
                "Fecha": fecha.strftime("%d/%m/%Y"),
                "Evento": tipo,
                "En_feriado": fecha in feriados_list,
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
                        "Cierre": random.choice(cierre)
                    }
                else:
                    sesion_dict["Planificacion"] = {
                        "Unidad": "",
                        "Contenido": "",
                        "Verbo": "",
                        "Concepto": "",
                        "Nivel": "",
                        "Actividad": "",
                        "Recursos": "",
                        "Evaluacion": "",
                        "Retroalimentacion": "",
                        "Introduccion": "",
                        "Inicio": "",
                        "Cierre": ""
                    }
                idx_normal += 1
            lista_sesiones_word.append(sesion_dict)

        # CONTEXTO PARA WORD
        context = {
            "PERIODO": f"{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}",
            "DIA_CLASE": dia_clase.capitalize(),
            "FERIADOS": ', '.join([f.strftime('%d/%m/%Y') for f in feriados_list]) if feriados_list else "",
            "PRUEBAS": ', '.join([f.strftime('%d/%m/%Y') for f in fechas_prueba]),
            "EXAMEN_FINAL": fecha_final_.strftime('%d/%m/%Y'),
            "UNIDADES": [u["titulo"] for u in unidades],
        }
        for sesion in lista_sesiones_word:
            pref = f"SESION_{sesion['Numero']}_"
            context[pref + "FECHA"] = sesion['Fecha']
            context[pref + "EVENTO"] = sesion['Evento']
            context[pref + "ADVERTENCIA"] = "⚠️ ¡Advertencia! Esta sesión coincide con un feriado." if sesion["En_feriado"] else ""
            planif = sesion.get("Planificacion")
            if planif:
                context[pref + "UNIDAD"] = f"🟢 UNIDAD : {planif['Unidad']}"
                context[pref + "CONTENIDO"] = f"📄 CONTENIDO: {planif['Contenido']}"
                context[pref + "OBJETIVO"] = f"🎯 OBJETIVO: El estudiante será capaz de {planif['Verbo']} {planif['Concepto']}"
                context[pref + "NIVEL_BLOOM"] = f"Nivel Bloom: {planif['Nivel']}"
                context[pref + "ESTRATEGIAS"] = f"Estrategias de aprendizaje: {planif['Actividad']}"
                context[pref + "RETROALIMENTACION"] = f"Retroalimentación: {planif['Retroalimentacion']}"
                context[pref + "INTRODUCCION"] = f"Introducción: {planif['Introduccion']}"
                context[pref + "INICIO"] = f"Inicio: {planif['Inicio']}"
                context[pref + "DESARROLLO"] = f"Desarrollo: {planif['Actividad']}"
                context[pref + "CIERRE"] = f"Cierre: {planif['Cierre']}"
                context[pref + "RECURSOS"] = f"Recursos: {planif['Recursos']}"
                context[pref + "EVALUACION"] = f"Evaluación: {planif['Evaluacion']}"
            else:
                for campo in ["UNIDAD","CONTENIDO","OBJETIVO","NIVEL_BLOOM","ESTRATEGIAS","RETROALIMENTACION","INTRODUCCION","INICIO",
                            "DESARROLLO","CIERRE","RECURSOS","EVALUACION"]:
                    context[pref + campo] = ""

        # Salida visual igual que antes, pero con títulos
        out = "\n📋 PLANIFICACIÓN SEMESTRAL\n"
        out += "=" * 90 + "\n"
        out += f"PERÍODO: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}\n"
        out += f"DÍA DE CLASE: {dia_clase.capitalize()}\n"
        if feriados_list: out += f"FERIADOS: {', '.join([f.strftime('%d/%m/%Y') for f in feriados_list])}\n"
        out += f"PRUEBAS: {', '.join([f.strftime('%d/%m/%Y') for f in fechas_prueba])}\n"
        out += f"EXAMEN FINAL: {fecha_final_.strftime('%d/%m/%Y')}\n"
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
                out += f"Desarrollo: {p['Actividad']}\n"
                out += f"Cierre: {p['Cierre']}\n"
                out += f"Recursos: {p['Recursos']}\n"
                out += f"Evaluación: {p['Evaluacion']}\n"
            if sesion["En_feriado"]:
                out += " ⚠️ ¡Advertencia! Esta sesión coincide con un feriado. Reagendar si es necesario.\n"
            out += "-" * 60 + "\n"

        st.success("¡Planificación generada! Consulta el informe y descarga los archivos abajo.")
        st.markdown("### Informe generado")
        st.text_area("Resumen", out, height=500)

        if plantilla_planeamiento is not None:
            doc_planeamiento = DocxTemplate(BytesIO(plantilla_planeamiento.read()))
            doc_planeamiento.render(context)
            buffer_planeamiento = BytesIO()
            doc_planeamiento.save(buffer_planeamiento)
            st.download_button("Descargar Planeamiento Word", buffer_planeamiento.getvalue(), file_name="Planeamiento.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        if plantilla_cronograma is not None:
            doc_cronograma = DocxTemplate(BytesIO(plantilla_cronograma.read()))
            doc_cronograma.render(context)
            buffer_cronograma = BytesIO()
            doc_cronograma.save(buffer_cronograma)
            st.download_button("Descargar Cronograma Word", buffer_cronograma.getvalue(), file_name="Cronograma.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        buffer_txt = BytesIO()
        buffer_txt.write(out.encode("utf-8"))
        buffer_txt.seek(0)
        st.download_button("Descargar Resumen TXT", buffer_txt.getvalue(), file_name="Planificacion.txt", mime="text/plain")

if __name__ == "__main__":
    main()