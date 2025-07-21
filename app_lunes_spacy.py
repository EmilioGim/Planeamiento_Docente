import streamlit as st
import random
import re
from datetime import datetime, timedelta
import os
import tempfile

# Intentar cargar spaCy
try:
    import spacy
    nlp = spacy.load("es_core_news_sm")
    SPACY_AVAILABLE = True
except (OSError, ImportError):
    st.warning("⚠️ spaCy no está disponible. Se usará procesamiento de texto básico.")
    SPACY_AVAILABLE = False
    nlp = None

# Configuración de la página
st.set_page_config(
    page_title="Planeamiento Semestral",
    page_icon="📚",
    layout="wide"
)

# Datos de referencia
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

dias_semana = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5}

def procesar_conceptos(texto):
    """Extrae conceptos del texto usando spaCy o procesamiento básico"""
    if SPACY_AVAILABLE and nlp:
        doc = nlp(texto.lower())
        conceptos = [chunk.text for chunk in doc.noun_chunks if len(chunk.text) > 2]
        return ", ".join(conceptos) if conceptos else texto.strip()
    else:
        # Procesamiento básico sin spaCy
        palabras = texto.split()
        palabras_filtradas = [p for p in palabras if len(p) > 3]
        return " ".join(palabras_filtradas[:3]) if palabras_filtradas else texto.strip()

def generar_planificacion(unidades_data, fecha_inicio, fecha_fin, dia_clase, feriados, pruebas, fecha_final):
    """Genera la planificación completa"""
    
    # Procesar unidades
    unidades = {}
    total_contenidos = 0
    
    for i, (titulo, contenidos) in enumerate(unidades_data):
        if not titulo.strip():
            titulo = f"Unidad {i+1}"
        lineas = [fr.strip() for fr in re.split(r'(?<=[.!?])\s+|\n', contenidos) if fr.strip()]
        unidades[titulo] = lineas
        total_contenidos += len(lineas)
    
    # Distribuir 10 sesiones proporcionalmente según la cantidad de contenidos
    total_sesiones_normales = 10
    sesiones_por_unidad = []
    sesiones_asignadas = 0
    
    # Calcular sesiones proporcionales
    unidades_list = list(unidades.items())
    for i, (titulo, frases) in enumerate(unidades_list):
        if i == len(unidades_list) - 1:  # Última unidad: asignar las sesiones restantes
            sesiones = total_sesiones_normales - sesiones_asignadas
        else:
            # Calcular proporción y asegurar al menos 1 sesión por unidad
            proporcion = len(frases) / total_contenidos if total_contenidos > 0 else 1/len(unidades_list)
            sesiones = max(1, round(proporcion * total_sesiones_normales))
        
        sesiones_por_unidad.append(sesiones)
        sesiones_asignadas += sesiones
    
    # Ajustar si hay diferencias por redondeo
    diferencia = total_sesiones_normales - sum(sesiones_por_unidad)
    if diferencia != 0:
        # Ajustar las unidades con más contenido
        indices_ordenados = sorted(range(len(unidades_list)), 
                                 key=lambda i: len(unidades_list[i][1]), reverse=True)
        for i in range(abs(diferencia)):
            idx = indices_ordenados[i % len(indices_ordenados)]
            if diferencia > 0:
                sesiones_por_unidad[idx] += 1
            elif sesiones_por_unidad[idx] > 1:  # No reducir por debajo de 1
                sesiones_por_unidad[idx] -= 1

    # Generar fragmentos de sesiones
    fragmentos_sesiones = []
    niveles = list(verbos_bloom.keys())
    nivel_idx = 0
    unidad_idx = 0
    
    for titulo, frases in unidades.items():
        cantidad_sesiones = sesiones_por_unidad[unidad_idx]
        
        # Distribuir contenidos de la unidad entre las sesiones asignadas
        if len(frases) == 0:
            frases = [f"Contenido de {titulo}"]  # Fallback si no hay contenidos
        
        # Dividir frases en grupos para cada sesión
        frases_por_sesion = len(frases) // cantidad_sesiones
        frases_extra = len(frases) % cantidad_sesiones
        
        inicio_idx = 0
        for s in range(cantidad_sesiones):
            # Calcular cuántas frases van en esta sesión
            frases_en_sesion = frases_por_sesion + (1 if s < frases_extra else 0)
            fin_idx = inicio_idx + frases_en_sesion
            
            # Tomar las frases correspondientes a esta sesión
            fragmento_frases = frases[inicio_idx:fin_idx]
            fragmento = " ".join(fragmento_frases) if fragmento_frases else f"Contenido {s+1} de {titulo}"
            
            concepto = procesar_conceptos(fragmento)
            
            nivel = niveles[nivel_idx % len(niveles)]
            verbo = random.choice(verbos_bloom[nivel])
            actividad = plantillas_actividades[nivel].format(concepto)
            
            fragmentos_sesiones.append({
                "Unidad": titulo,
                "Contenido": fragmento,
                "Concepto": concepto,
                "Nivel": nivel,
                "Verbo": verbo,
                "Actividad": actividad,
                "Recursos": ", ".join(recursos_bloom[nivel]),
                "Evaluacion": ", ".join(evaluacion_bloom[nivel]),
                "Sesiones_Unidad": cantidad_sesiones,  # Para debug
                "Sesion_En_Unidad": s + 1  # Para debug
            })
            nivel_idx += 1
            inicio_idx = fin_idx
        
        unidad_idx += 1

    # Generar calendario
    dia_clase_num = dias_semana[dia_clase]
    
    # Calcular fechas de sesiones
    sesiones_fechas = []
    for i in range(17):
        base = fecha_inicio + timedelta(weeks=i)
        sesion_date = base + timedelta(days=(dia_clase_num - base.weekday()) % 7)
        sesiones_fechas.append(sesion_date)
    
    # Identificar sesiones especiales
    prueba_idxs = [sesiones_fechas.index(dt) for dt in pruebas if dt in sesiones_fechas]
    retro_sesiones = []
    revision_sesiones = []
    
    for idx in prueba_idxs:
        if idx > 0: 
            retro_sesiones.append(idx - 1)
        if idx + 1 < len(sesiones_fechas):
            revision_sesiones.append(idx + 1)
    
    final_idx = sesiones_fechas.index(fecha_final) if fecha_final in sesiones_fechas else 16

    # Planificación semanal completa
    plan_semanal = []
    j = 0
    
    for i in range(17):
        dia_evento = sesiones_fechas[i]
        en_feriado = dia_evento in feriados
        
        if i == final_idx:
            estado = "Examen final"
        elif i in prueba_idxs:
            estado = "Prueba parcial"
        elif i in retro_sesiones:
            estado = "Retroalimentación"
        elif i in revision_sesiones:
            estado = "Revisión de prueba"
        else:
            estado = "Clase normal"
        
        plan_semanal.append({
            "Sesion": i+1,
            "Fecha": dia_evento,
            "Evento": estado,
            "Planificacion": None,
            "En_feriado": en_feriado
        })
        
        if estado == "Clase normal" and j < len(fragmentos_sesiones):
            plan_semanal[i]["Planificacion"] = fragmentos_sesiones[j]
            j += 1

    return plan_semanal, unidades

def generar_texto_planificacion(plan_semanal, unidades, fecha_inicio, fecha_fin, dia_clase, feriados, pruebas, fecha_final):
    """Genera el texto completo de la planificación"""
    
    out = "\n📋 PLANIFICACIÓN SEMESTRAL\n"
    out += "=" * 90 + "\n"
    out += f"PERÍODO: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}\n"
    out += f"DÍA DE CLASE: {dia_clase}\n"
    
    if feriados: 
        out += f"FERIADOS: {', '.join([f.strftime('%d/%m/%Y') for f in feriados])}\n"
    if pruebas: 
        out += f"PRUEBAS: {', '.join([f.strftime('%d/%m/%Y') for f in pruebas])}\n"
    
    out += f"EXAMEN FINAL: {fecha_final.strftime('%d/%m/%Y')}\n"
    out += "\n" + "-" * 90 + "\n"
    out += "UNIDADES PROGRAMADAS:\n"
    
    for i, (titulo, contenidos) in enumerate(unidades.items(), 1):
        out += f"{i}. {titulo}\n"
        for contenido in contenidos:
            out += f"   - {contenido}\n"
        out += "\n"
    
    out += "=" * 90 + "\n"
    out += "\n📅 SESIONES DEL SEMESTRE:\n"
    
    for sesion in plan_semanal:
        out += f"\n🔵 SESIÓN {sesion['Sesion']:02d} | {sesion['Fecha'].strftime('%d/%m/%Y')} | {sesion['Evento']}\n"
        out += "-" * 60 + "\n"
        
        if sesion["Evento"] == "Clase normal" and sesion["Planificacion"]:
            p = sesion["Planificacion"]
            out += f"🟢 UNIDAD : {p['Unidad']}\n"
            out += f"📄 CONTENIDO: {p['Contenido']}\n"
            out += f"🎯 OBJETIVO: El estudiante será capaz de {p['Verbo']} {p['Concepto']}\n"
            out += f"🪜 NIVEL BLOOM: {p['Nivel']}\n"
            out += f"📌 MOMENTOS DIDÁCTICOS:\n"
            out += f" ▪ Retroalimentación: {random.choice(retro)}\n"
            out += f" ▪ Introducción: {random.choice(intro)}\n"
            out += f" ▪ Inicio: {random.choice(inicio)}\n"
            out += f" ▪ Desarrollo: {p['Actividad']}\n"
            out += f" ▪ Cierre: {random.choice(cierre)}\n"
            out += f"🧰 RECURSOS: {p['Recursos']}\n"
            out += f"📝 EVALUACIÓN: {p['Evaluacion']}\n"
        
        if sesion["En_feriado"]:
            out += " ⚠️ ¡Advertencia! Esta sesión coincide con un feriado. Reagendar si es necesario.\n"
        
        out += "-" * 60 + "\n"
    
    return out

def main():
    st.title("📚 Planeamiento Semestral")
    st.markdown("### Generador basado en Taxonomía de Bloom + spaCy")
    
    if not SPACY_AVAILABLE:
        st.info("💡 Para obtener mejor extracción de conceptos, instala spaCy: `pip install spacy` y luego `python -m spacy download es_core_news_sm`")
    
    # Sidebar para configuración
    st.sidebar.header("⚙️ Configuración")
    
    # Número de unidades
    num_unidades = st.sidebar.slider("¿Cuántas unidades?", 1, 10, 5)
    
    # Sección principal - Unidades
    st.header("📖 Definir Unidades")
    
    unidades_data = []
    for i in range(num_unidades):
        with st.expander(f"Unidad {i+1}", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                titulo = st.text_input(f"Título", value=f"Unidad {i+1}", key=f"titulo_{i}")
            with col2:
                contenidos = st.text_area(
                    f"Contenidos (párrafos, puntos, etc)", 
                    height=100,
                    key=f"contenidos_{i}",
                    help="Escribe los contenidos separados por puntos o párrafos"
                )
            unidades_data.append((titulo, contenidos))
    
    # Configuración de fechas
    st.header("📅 Configuración de Fechas")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", datetime.now().date())
        fecha_fin = st.date_input("Fecha de fin", datetime.now().date() + timedelta(weeks=17))
        dia_clase = st.selectbox("Día de clase", list(dias_semana.keys()))
    
    with col2:
        st.subheader("Fechas especiales")
        prueba1 = st.date_input("Prueba 1 (opcional)", value=None)
        prueba2 = st.date_input("Prueba 2 (opcional)", value=None)
        fecha_final = st.date_input("Examen final", datetime.now().date() + timedelta(weeks=16))
    
    # Feriados
    st.subheader("🎉 Feriados")
    feriados_text = st.text_area(
        "Fechas de feriados (una por línea, formato DD/MM/AAAA)",
        help="Ejemplo:\n01/01/2024\n15/08/2024"
    )
    
    # Procesar feriados
    feriados = []
    if feriados_text.strip():
        for linea in feriados_text.strip().split('\n'):
            try:
                fecha = datetime.strptime(linea.strip(), '%d/%m/%Y').date()
                feriados.append(fecha)
            except ValueError:
                st.warning(f"Formato de fecha inválido: {linea}")
    
    # Procesar pruebas
    pruebas = []
    if prueba1:
        pruebas.append(prueba1)
    if prueba2:
        pruebas.append(prueba2)
    
    # Botón para generar
    if st.button("🚀 Generar Planificación", type="primary"):
        # Validaciones
        if fecha_inicio >= fecha_fin:
            st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
            return
        
        if not any(contenidos.strip() for _, contenidos in unidades_data):
            st.error("Debe completar al menos una unidad con contenidos.")
            return
        
        try:
            # Generar planificación
            with st.spinner("Generando planificación..."):
                plan_semanal, unidades = generar_planificacion(
                    unidades_data, fecha_inicio, fecha_fin, dia_clase, 
                    feriados, pruebas, fecha_final
                )
                
                texto_completo = generar_texto_planificacion(
                    plan_semanal, unidades, fecha_inicio, fecha_fin, 
                    dia_clase, feriados, pruebas, fecha_final
                )
            
            st.success("¡Planificación generada exitosamente!")
            
            # Mostrar resultados
            st.header("📋 Planificación Generada")
            
            # Mostrar en texto
            st.text_area("Planificación completa", texto_completo, height=400)
            
            # Botón de descarga
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Planificacion_{timestamp}.txt"
            
            st.download_button(
                label="📥 Descargar Planificación (TXT)",
                data=f"PLANIFICACIÓN DOCENTE - GENERADA EL {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n" + 
                     "=" * 90 + "\n" + texto_completo,
                file_name=filename,
                mime="text/plain"
            )
            
            # Mostrar resumen en cards
            st.header("📊 Resumen")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Unidades", len(unidades))
            with col2:
                clases_normales = len([s for s in plan_semanal if s["Evento"] == "Clase normal"])
                st.metric("Clases Normales", clases_normales)
            with col3:
                st.metric("Pruebas", len(pruebas))
            with col4:
                feriados_coincidentes = len([s for s in plan_semanal if s["En_feriado"]])
                st.metric("Coincidencias c/Feriados", feriados_coincidentes)
            
            # Mostrar distribución de sesiones por unidad
            st.subheader("📈 Distribución de Sesiones por Unidad")
            
            # Calcular sesiones por unidad para mostrar
            distribucion_info = []
            for i, (titulo, contenidos_lista) in enumerate(unidades.items()):
                sesiones_unidad = len([p for p in plan_semanal if p.get("Planificacion") and p["Planificacion"]["Unidad"] == titulo])
                contenidos_count = len(contenidos_lista)
                distribucion_info.append({
                    "Unidad": titulo,
                    "Contenidos": contenidos_count,
                    "Sesiones Asignadas": sesiones_unidad
                })
            
            for info in distribucion_info:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**{info['Unidad']}**")
                with col2:
                    st.write(f"Contenidos: {info['Contenidos']}")
                with col3:
                    st.write(f"Sesiones: {info['Sesiones Asignadas']}")
            
            # Mostrar calendario de sesiones
            st.header("📅 Calendario de Sesiones")
            
            for sesion in plan_semanal:
                fecha_str = sesion['Fecha'].strftime('%d/%m/%Y')
                
                if sesion["Evento"] == "Clase normal":
                    color = "🟢"
                elif sesion["Evento"] == "Prueba parcial":
                    color = "🔴"
                elif sesion["Evento"] == "Examen final":
                    color = "🟡"
                else:
                    color = "🔵"
                
                feriado_warning = " ⚠️ FERIADO" if sesion["En_feriado"] else ""
                
                with st.expander(f"{color} Sesión {sesion['Sesion']:02d} - {fecha_str} - {sesion['Evento']}{feriado_warning}"):
                    if sesion["Evento"] == "Clase normal" and sesion["Planificacion"]:
                        p = sesion["Planificacion"]
                        st.write(f"**Unidad:** {p['Unidad']}")
                        st.write(f"**Contenido:** {p['Contenido']}")
                        st.write(f"**Objetivo:** El estudiante será capaz de {p['Verbo']} {p['Concepto']}")
                        st.write(f"**Nivel Bloom:** {p['Nivel']}")
                        st.write(f"**Actividad:** {p['Actividad']}")
                        st.write(f"**Recursos:** {p['Recursos']}")
                        st.write(f"**Evaluación:** {p['Evaluacion']}")
                    else:
                        st.write(f"**Tipo de sesión:** {sesion['Evento']}")
                    
                    if sesion["En_feriado"]:
                        st.warning("Esta sesión coincide con un feriado. Considere reagendar.")
                        
        except Exception as e:
            st.error(f"Error al generar la planificación: {str(e)}")
            st.write("Detalles del error:", str(e))

if __name__ == "__main__":
    main()