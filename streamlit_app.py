import streamlit as st
import random
import re
from datetime import datetime, timedelta
from collections import defaultdict
import os
import zipfile
import io
import hashlib
import json

# Importar NLTK como reemplazo de spaCy
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
    from nltk.tree import Tree
    
    # Descargar recursos necesarios si no están disponibles
    nltk_downloads = ['punkt', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words', 'stopwords']
    for resource in nltk_downloads:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except:
                pass
                
except ImportError:
    st.error("NLTK no está instalado. Por favor instale con: pip install nltk")
    st.stop()

try:
    from docxtpl import DocxTemplate
except ImportError:
    st.error("python-docx-template no está instalado. Por favor instale con: pip install python-docx-template")
    st.stop()

# === Sistema de autenticación ===
def cargar_usuarios():
    """Carga usuarios desde archivo JSON"""
    archivo_usuarios = "usuarios.json"
    
    # Crear archivo por defecto si no existe
    if not os.path.exists(archivo_usuarios):
        usuarios_default = {
            "admin": {
                "password": "admin123",
                "privilegio": "Completo"
            },
            "profesor": {
                "password": "prof456",
                "privilegio": "Estándar"
            },
            "coordinador": {
                "password": "coord789",
                "privilegio": "Completo"
            },
            "docente1": {
                "password": "doc123",
                "privilegio": "Estándar"
            },
             "yudith": {
                "password": "yudithdra01",
                "privilegio": "Estándar"
    }
        }
        
        with open(archivo_usuarios, 'w', encoding='utf-8') as f:
            json.dump(usuarios_default, f, indent=2, ensure_ascii=False)
    
    # Cargar usuarios del archivo
    try:
        with open(archivo_usuarios, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        st.error(f"Error al cargar el archivo {archivo_usuarios}")
        return {}

def verificar_credenciales(usuario, password):
    """Verifica las credenciales del usuario"""
    usuarios = cargar_usuarios()
    if usuario in usuarios:
        return usuarios[usuario]["password"] == password, usuarios[usuario].get("privilegio", "Estándar")
    return False, None

def cargar_plantillas():
    """Carga plantillas desde el subdirectorio templates"""
    templates_dir = "templates"
    plantilla_planeamiento = None
    plantilla_cronograma = None
    
    if os.path.exists(templates_dir):
        # Buscar plantilla de planeamiento
        planeamiento_path = os.path.join(templates_dir, "plantilla_planeamiento.docx")
        if os.path.exists(planeamiento_path):
            with open(planeamiento_path, 'rb') as f:
                plantilla_planeamiento = f.read()
        
        # Buscar plantilla de cronograma
        cronograma_path = os.path.join(templates_dir, "plantilla_cronograma.docx")
        if os.path.exists(cronograma_path):
            with open(cronograma_path, 'rb') as f:
                plantilla_cronograma = f.read()
    
    return plantilla_planeamiento, plantilla_cronograma

def mostrar_login():
    """Muestra la pantalla de login"""
    st.title("🔐 Planificador de Clases - Inicio de Sesión")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("Ingrese sus credenciales")
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
        
        if submit:
            es_valido, privilegio = verificar_credenciales(usuario, password)
            if es_valido:
                st.session_state.authenticated = True
                st.session_state.usuario = usuario
                st.session_state.privilegio = privilegio
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    
    st.markdown("---")
    st.info("**Contacte al administrador para obtener credenciales de acceso**")

# === Recursos y plantillas Bloom ===
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
    "viernes": 4
}

dias_semana_es = {
    0: "Lunes",
    1: "Martes", 
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

meses_es = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# === Funciones de procesamiento de texto con NLTK ===
def extraer_conceptos_nltk(texto):
    """
    Extrae conceptos clave del texto usando NLTK como reemplazo de spaCy
    Mejorado para extraer frases completas en lugar de palabras individuales
    """
    try:
        # Dividir en frases
        frases = [frase.strip() for frase in re.split(r'[,;\n]', texto) if frase.strip()]
        
        if frases:
            # Tomar la primera frase completa como concepto principal
            concepto_principal = frases[0].strip()
            # Limpiar puntuación al final
            concepto_principal = re.sub(r'[\.!?]+$', '', concepto_principal)
            return [concepto_principal]
        
        # Si no hay frases separadas por comas, usar el texto completo
        concepto_limpio = re.sub(r'[\.!?]+$', '', texto.strip())
        return [concepto_limpio] if concepto_limpio else [texto.strip()]
        
    except Exception as e:
        # En caso de error, devolver el texto original
        return [texto.strip()]

# === Funciones auxiliares ===
def genera_dict_unidades(unidades_data):
    """Genera diccionario de unidades desde los datos de entrada"""
    unidades = {}
    for i, (titulo, contenidos) in enumerate(unidades_data):
        if not titulo.strip():
            titulo = f"Unidad {i+1}"
        
        if not contenidos.strip():
            continue
            
        lineas = [fr.strip() for fr in contenidos.split('\n') if fr.strip()]
        if len(lineas) == 1:
            # Split by sentence if it's a single line of text
            frases = [fr.strip() for fr in re.split(r'(?<=[.!?])\s+', lineas[0]) if fr.strip()]
        else:
            # Treat each line as a "phrase" if multiple lines are entered
            frases = lineas
        unidades[titulo] = frases
    return unidades

def ajustar_unidades_para_sesiones(unidades_originales, total_sesiones_normales=10):
    """
    Ajusta las unidades para que se adapten al número de sesiones disponibles
    """
    n_original = len(unidades_originales)
    
    # Crear lista de bloques de sesión
    lista_bloques_sesion = []
    for i, (titulo, frases) in enumerate(unidades_originales.items()):
        lista_bloques_sesion.append({
            "titulo": titulo,
            "frases": frases,
            "longitud": len(frases)
        })
    
    # Lógica de ajuste
    if n_original < total_sesiones_normales:
        # Fraccionar unidades
        sesiones_por_unidad_calc = [total_sesiones_normales // n_original] * n_original
        for i in range(total_sesiones_normales % n_original):
            sesiones_por_unidad_calc[i] += 1
        
        expanded_bloques = []
        for idx, bloque_original in enumerate(lista_bloques_sesion):
            cantidad_sesiones_para_unidad = sesiones_por_unidad_calc[idx]
            frases_unidad = bloque_original["frases"]
            
            por_sesion = max(1, len(frases_unidad) // cantidad_sesiones_para_unidad) if cantidad_sesiones_para_unidad > 0 else 1
            
            for s in range(cantidad_sesiones_para_unidad):
                fragmento_frases = frases_unidad[s*por_sesion:(s+1)*por_sesion]
                
                if not fragmento_frases:
                    fragmento_frases = [frases_unidad[-1]] if frases_unidad else [f"Contenido de {bloque_original['titulo']}"]
                
                expanded_bloques.append({
                    "titulo": f"{bloque_original['titulo']} (Parte {s+1}/{cantidad_sesiones_para_unidad})" if cantidad_sesiones_para_unidad > 1 else bloque_original['titulo'],
                    "frases": fragmento_frases,
                    "longitud": len(fragmento_frases)
                })
        lista_bloques_sesion = expanded_bloques
        
    elif n_original > total_sesiones_normales:
        # Fusionar unidades
        num_fusiones_necesarias = n_original - total_sesiones_normales
        
        for _ in range(num_fusiones_necesarias):
            if len(lista_bloques_sesion) <= total_sesiones_normales:
                break
            
            min_len_combined = float('inf')
            idx_to_merge = -1
            
            for i in range(len(lista_bloques_sesion) - 1):
                len_combined = lista_bloques_sesion[i]["longitud"] + lista_bloques_sesion[i+1]["longitud"]
                if len_combined < min_len_combined:
                    min_len_combined = len_combined
                    idx_to_merge = i
            
            if idx_to_merge != -1:
                unidad1 = lista_bloques_sesion[idx_to_merge]
                unidad2 = lista_bloques_sesion[idx_to_merge + 1]
                
                nuevo_titulo = f"{unidad1['titulo']} - {unidad2['titulo']}"
                nuevo_contenido = unidad1['frases'] + unidad2['frases']
                nueva_longitud = len(nuevo_contenido)
                
                lista_bloques_sesion[idx_to_merge] = {
                    "titulo": nuevo_titulo,
                    "frases": nuevo_contenido,
                    "longitud": nueva_longitud
                }
                lista_bloques_sesion.pop(idx_to_merge + 1)
            else:
                break
    
    return lista_bloques_sesion

def generar_planificacion_calendario(fecha_inicio_dt, dia_clase_num, fecha_examen_final, feriados, pruebas, retro_sesiones, revision_sesiones):
    """Genera la planificación del calendario"""
    plan = []
    sesion_num = 1
    while sesion_num <= 17:
        if sesion_num == 17:
            dia_evento = fecha_examen_final
            estado = "Examen final"
            en_feriado = dia_evento in feriados
        else:
            fecha_base = fecha_inicio_dt + timedelta(weeks=sesion_num - 1)
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

def formatear_fecha_es(fecha):
    """Formatea fecha en español"""
    # Manejar diferentes tipos de entrada
    if isinstance(fecha, tuple):
        fecha = fecha[0] if fecha else None
    
    if not fecha or not hasattr(fecha, 'weekday'):
        return "Fecha inválida"
    
    dia_sem = dias_semana_es[fecha.weekday()]
    mes = meses_es[fecha.month]
    return f"{dia_sem}, {fecha.day} de {mes} de {fecha.year}"

def crear_archivo_zip(context, context_cronograma, plantilla_planeamiento, plantilla_cronograma, out_text, unidades_originales, configuracion):
    """Crea un archivo ZIP con todos los documentos generados"""
    zip_buffer = io.BytesIO()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        try:
            # Generar archivo de Planeamiento
            if plantilla_planeamiento:
                doc_planeamiento = DocxTemplate(io.BytesIO(plantilla_planeamiento))
                doc_planeamiento.render(context)
                docx_buffer = io.BytesIO()
                doc_planeamiento.save(docx_buffer)
                zip_file.writestr(f"Planeamiento_{timestamp}.docx", docx_buffer.getvalue())
            
            # Generar archivo de Cronograma
            if plantilla_cronograma:
                doc_cronograma = DocxTemplate(io.BytesIO(plantilla_cronograma))
                doc_cronograma.render(context_cronograma)
                cronograma_buffer = io.BytesIO()
                doc_cronograma.save(cronograma_buffer)
                zip_file.writestr(f"Cronograma_{timestamp}.docx", cronograma_buffer.getvalue())
            
            # Generar archivo TXT
            txt_content = f"PLANIFICACIÓN DOCENTE - GENERADA EL {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            txt_content += "=" * 80 + "\n"
            txt_content += f"PERÍODO: {configuracion['fecha_inicio']} al {configuracion['fecha_fin']}\n"
            txt_content += f"DÍA DE CLASE: {configuracion['dia_clase'].capitalize()}\n"
            
            # Manejar feriados correctamente
            if configuracion['feriados']:
                feriados_str = []
                for f in configuracion['feriados']:
                    if hasattr(f, 'strftime'):
                        feriados_str.append(f.strftime('%Y-%m-%d'))
                    else:
                        feriados_str.append(str(f))
                txt_content += f"FERIADOS: {', '.join(feriados_str)}\n"
            
            if configuracion['pruebas']:
                txt_content += f"PRUEBAS EN SESIONES: {', '.join(map(str, configuracion['pruebas']))}\n"
            txt_content += f"EXAMEN FINAL: {configuracion['fecha_examen_final']}\n"
            txt_content += "\n" + "=" * 80 + "\n"
            txt_content += "UNIDADES PROGRAMADAS:\n"
            txt_content += "-" * 40 + "\n"
            for i, (titulo, contenidos) in enumerate(unidades_originales.items(), 1):
                txt_content += f"{i}. {titulo}\n"
                for contenido in contenidos:
                    txt_content += f"   - {contenido}\n"
                txt_content += "\n"
            txt_content += "=" * 80 + "\n"
            txt_content += out_text
            txt_content += "\n" + "=" * 80 + "\n"
            txt_content += "ARCHIVOS GENERADOS:\n"
            txt_content += f"- Planeamiento: Planeamiento_{timestamp}.docx\n"
            txt_content += f"- Cronograma: Cronograma_{timestamp}.docx\n"
            txt_content += f"- Resumen TXT: Planificacion_{timestamp}.txt\n"
            
            zip_file.writestr(f"Planificacion_{timestamp}.txt", txt_content.encode('utf-8'))
            
        except Exception as e:
            st.error(f"Error al generar los archivos: {str(e)}")
            return None
    
    zip_buffer.seek(0)
    return zip_buffer

def crear_archivo_txt(out_text, unidades_originales, configuracion):
    """Crea solo el archivo TXT para usuarios estándar"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    txt_content = f"PLANIFICACIÓN DOCENTE - GENERADA EL {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    txt_content += "=" * 80 + "\n"
    txt_content += f"PERÍODO: {configuracion['fecha_inicio']} al {configuracion['fecha_fin']}\n"
    txt_content += f"DÍA DE CLASE: {configuracion['dia_clase'].capitalize()}\n"
    
    # Manejar feriados correctamente
    if configuracion['feriados']:
        feriados_str = []
        for f in configuracion['feriados']:
            if hasattr(f, 'strftime'):
                feriados_str.append(f.strftime('%Y-%m-%d'))
            else:
                feriados_str.append(str(f))
        txt_content += f"FERIADOS: {', '.join(feriados_str)}\n"
    
    if configuracion['pruebas']:
        txt_content += f"PRUEBAS EN SESIONES: {', '.join(map(str, configuracion['pruebas']))}\n"
    txt_content += f"EXAMEN FINAL: {configuracion['fecha_examen_final']}\n"
    txt_content += "\n" + "=" * 80 + "\n"
    txt_content += "UNIDADES PROGRAMADAS:\n"
    txt_content += "-" * 40 + "\n"
    for i, (titulo, contenidos) in enumerate(unidades_originales.items(), 1):
        txt_content += f"{i}. {titulo}\n"
        for contenido in contenidos:
            txt_content += f"   - {contenido}\n"
        txt_content += "\n"
    txt_content += "=" * 80 + "\n"
    txt_content += out_text
    
    return txt_content.encode('utf-8'), f"Planificacion_{timestamp}.txt"

# === APLICACIÓN STREAMLIT ===
def main():
    st.set_page_config(
        page_title="Planificador de Clases (Bloom)",
        page_icon="📚",
        layout="wide"
    )
    
    # Verificar autenticación
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        mostrar_login()
        return
    
    # Agregar información del usuario en la sidebar
    with st.sidebar:
        st.write(f"👤 Usuario: **{st.session_state.usuario}**")
        st.write(f"🔐 Privilegio: **{st.session_state.privilegio}**")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.authenticated = False
            st.session_state.clear()
            st.rerun()
        st.markdown("---")
    
    st.title("📚 Planificador de Clases (Taxonomía de Bloom)")
    st.markdown("---")
    
    # Inicializar session state
    if 'unidades_data' not in st.session_state:
        st.session_state.unidades_data = [("Unidad 1", ""), ("Unidad 2", "")]
    
    # Cargar plantillas automáticamente
    plantilla_planeamiento, plantilla_cronograma = cargar_plantillas()
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Número de unidades
        num_unidades = st.number_input(
            "¿Cuántas unidades?",
            min_value=1,
            max_value=20,
            value=len(st.session_state.unidades_data),
            step=1
        )
        
        # Ajustar la lista de unidades según el número seleccionado
        while len(st.session_state.unidades_data) < num_unidades:
            st.session_state.unidades_data.append((f"Unidad {len(st.session_state.unidades_data)+1}", ""))
        while len(st.session_state.unidades_data) > num_unidades:
            st.session_state.unidades_data.pop()
        
        st.markdown("---")
        
        # Fechas del curso
        st.subheader("📅 Calendario del Curso")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha de inicio")
        with col2:
            fecha_fin = st.date_input("Fecha de fin")
        
        dia_clase = st.selectbox("Día de clase", list(dias_semana.keys()))
        
        # Fechas especiales
        st.subheader("📋 Fechas Especiales")
        
        # Calendario para feriados
        st.write("**Feriados:**")
        feriados_input = st.date_input(
            "Seleccione feriados",
            value=[],
            key="feriados_calendar"
        )
        
        # Convertir a lista si es necesario
        if not isinstance(feriados_input, list):
            feriados_input = [feriados_input] if feriados_input else []
        
        # Selección de pruebas parciales (exactamente 2)
        st.write("**Pruebas Parciales (seleccione 2 sesiones):**")
        prueba1 = st.selectbox("Primera prueba parcial (sesión)", 
                               options=list(range(1, 17)), 
                               index=4,  # sesión 5 por defecto
                               key="prueba1")
        prueba2 = st.selectbox("Segunda prueba parcial (sesión)", 
                               options=list(range(1, 17)), 
                               index=9,  # sesión 10 por defecto
                               key="prueba2")
        
        # Validar que las pruebas no sean iguales
        if prueba1 == prueba2:
            st.error("Las dos pruebas parciales deben ser en sesiones diferentes")
        
        fecha_examen_final = st.date_input("Fecha del examen final")
        
        st.markdown("---")
        
        # Estado de plantillas
        st.subheader("📄 Estado de Plantillas")
        if plantilla_planeamiento:
            st.success("✅ Plantilla planeamiento cargada")
        else:
            st.warning("⚠️ Plantilla planeamiento no encontrada")
        
        if plantilla_cronograma:
            st.success("✅ Plantilla cronograma cargada")
        else:
            st.warning("⚠️ Plantilla cronograma no encontrada")
        
        if not plantilla_planeamiento and not plantilla_cronograma:
            st.info("💡 Coloque las plantillas en la carpeta 'templates/'")
    
    # Contenido principal
    st.header("📖 Unidades del Curso")
    
    # Editor de unidades
    for i in range(num_unidades):
        with st.expander(f"Unidad {i+1}", expanded=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                titulo = st.text_input(
                    "Título de la unidad",
                    value=st.session_state.unidades_data[i][0],
                    key=f"titulo_{i}"
                )
            
            with col2:
                contenidos = st.text_area(
                    "Contenidos (una línea por ítem)",
                    value=st.session_state.unidades_data[i][1],
                    height=100,
                    key=f"contenidos_{i}"
                )
            
            # Actualizar session state
            st.session_state.unidades_data[i] = (titulo, contenidos)
    
    st.markdown("---")
    
    # Botón para generar planificación
    if st.button("🚀 Generar Planificación", type="primary", use_container_width=True):
        
        # Validaciones
        errores = []
        
        if fecha_inicio >= fecha_fin:
            errores.append("La fecha de inicio debe ser anterior a la fecha de fin")
        
        if fecha_examen_final <= fecha_fin:
            errores.append("La fecha del examen final debe ser posterior a la fecha de fin del curso")
        
        if prueba1 == prueba2:
            errores.append("Las dos pruebas parciales deben ser en sesiones diferentes")
        
        # Verificar que hay contenido en las unidades
        unidades_vacias = 0
        for titulo, contenidos in st.session_state.unidades_data:
            if not contenidos.strip():
                unidades_vacias += 1
        
        if unidades_vacias == len(st.session_state.unidades_data):
            errores.append("Debe ingresar contenido en al menos una unidad")
        
        if errores:
            for error in errores:
                st.error(error)
            return
        
        # Procesar fechas especiales - Manejar múltiples feriados correctamente
        feriados = []
        if feriados_input:
            if isinstance(feriados_input, (list, tuple)):
                # Filtrar y procesar cada fecha
                for fecha in feriados_input:
                    if isinstance(fecha, tuple):
                        # Si es tupla, tomar el primer elemento válido
                        fecha = fecha[0] if fecha and len(fecha) > 0 else None
                    if fecha and hasattr(fecha, 'strftime'):
                        feriados.append(fecha)
            else:
                # Fecha única
                if hasattr(feriados_input, 'strftime'):
                    feriados = [feriados_input]
        
        # Usar las pruebas seleccionadas
        pruebas = [prueba1, prueba2]
        retro_sesiones = [p - 1 for p in pruebas if p > 1]
        revision_sesiones = [p + 1 for p in pruebas if p < 16]
        
        # Generar planificación
        with st.spinner("Generando planificación..."):
            
            # Generar diccionario de unidades
            unidades_originales = genera_dict_unidades(st.session_state.unidades_data)
            
            # Calcular sesiones normales disponibles
            sesiones_especiales = len(pruebas) + len(retro_sesiones) + len(revision_sesiones)
            sesiones_normales_disponibles = 16 - sesiones_especiales  # 16 porque la 17 es examen final
            
            # Ajustar unidades para sesiones normales disponibles
            lista_bloques_sesion = ajustar_unidades_para_sesiones(unidades_originales, sesiones_normales_disponibles)
            
            # Procesar fragmentos para sesiones normales
            fragmentos_sesiones = []
            niveles = list(verbos_bloom.keys())
            nivel_idx = 0
            
            for idx, bloque_sesion in enumerate(lista_bloques_sesion):
                unidad_titulo = bloque_sesion["titulo"]
                frases = bloque_sesion["frases"]
                
                if not frases:
                    continue
                
                fragmento = " ".join(frases)
                
                # Procesamiento con NLTK mejorado
                conceptos = extraer_conceptos_nltk(fragmento)
                concepto = conceptos[0] if conceptos else fragmento.strip()
                
                nivel = niveles[nivel_idx % len(niveles)]
                verbo = random.choice(verbos_bloom[nivel])
                actividad = plantillas_actividades[nivel].format(concepto)
                
                fragmentos_sesiones.append({
                    "Unidad": unidad_titulo,
                    "Contenido": fragmento,
                    "Concepto": concepto,
                    "Nivel": nivel,
                    "Verbo": verbo,
                    "Actividad": actividad,
                    "Nivel_idx": nivel_idx
                })
                nivel_idx += 1
            
            # Generar planificación del calendario
            plan_semanal = generar_planificacion_calendario(
                fecha_inicio, dias_semana[dia_clase], fecha_examen_final,
                feriados, pruebas, retro_sesiones, revision_sesiones
            )
            
            sesiones_normales_idx = [i for i, s in enumerate(plan_semanal) if s["Evento"] == "Clase normal"]
            
            # Asignar contenido a sesiones
            if len(sesiones_normales_idx) < len(fragmentos_sesiones):
                st.warning("⚠️ Hay menos sesiones normales disponibles que unidades ajustadas. Algunas unidades no serán asignadas.")
                total_asignar = len(sesiones_normales_idx)
            else:
                total_asignar = len(fragmentos_sesiones)
            
            if not fragmentos_sesiones:
                st.error("No se pudo generar ningún fragmento de unidad. Verifique el contenido ingresado.")
                return
            
            for idx, frag_idx in enumerate(range(total_asignar)):
                i = sesiones_normales_idx[idx]
                plan_semanal[i]["Planificacion"] = fragmentos_sesiones[frag_idx]
            
            # Generar texto de salida mejorado
            out = "\n📋 Planificación semanal completa:\n"
            out += "=" * 80 + "\n"
            for sesion in plan_semanal:
                fecha_formateada = formatear_fecha_es(sesion['Fecha'])
                out += f"Sesión {sesion['Sesion']:2d} | {fecha_formateada} | {sesion['Evento']}\n"
                if sesion["Evento"] == "Clase normal" and "Planificacion" in sesion:
                    p = sesion["Planificacion"]
                    out += f" 🟢 Unidad: {p['Unidad']}\n"
                    out += f" 📄 Contenido: {p['Contenido']}\n"
                    out += f" 🎯 Objetivo: El estudiante será capaz de {p['Verbo']} {p['Concepto']}\n"
                    out += f" 🪜 Nivel Bloom: {p['Nivel']}\n"
                    out += f" 📌 Momentos Didácticos:\n"
                    out += f" ▪ Retroalimentación: {random.choice(retro)}\n"
                    out += f" ▪ Introducción: {random.choice(intro)}\n"
                    out += f" ▪ Inicio: {random.choice(inicio)}\n"
                    out += f" ▪ Desarrollo: {p['Actividad']}\n"
                    out += f" ▪ Cierre: {random.choice(cierre)}\n"
                    out += f" 🧰 Recursos: {', '.join(recursos_bloom[p['Nivel']])}\n"
                    out += f" 📝 Evaluación: {', '.join(evaluacion_bloom[p['Nivel']])}\n"
                elif sesion["Evento"] == "Prueba parcial":
                    out += f" 📝 Evaluación parcial programada\n"
                elif sesion["Evento"] == "Retroalimentación":
                    out += f" 🔄 Sesión de retroalimentación pre-prueba\n"
                elif sesion["Evento"] == "Revisión de prueba":
                    out += f" 📊 Revisión y análisis de resultados de prueba\n"
                elif sesion["Evento"] == "Examen final":
                    out += f" 🎓 Evaluación final del curso\n"
                if sesion["En_feriado"]:
                    out += " ⚠️ ¡Advertencia! Esta sesión coincide con un feriado. Reagendar si es necesario.\n"
                out += "-" * 70 + "\n"
            
            # Mostrar resultado en la interfaz
            st.success("¡Planificación generada exitosamente!")
            
            # Mostrar planificación en expander
            with st.expander("📋 Ver Planificación Completa", expanded=True):
                st.text(out)
            
            # Configuración para archivos
            configuracion = {
                'fecha_inicio': fecha_inicio.strftime("%Y-%m-%d"),
                'fecha_fin': fecha_fin.strftime("%Y-%m-%d"),
                'dia_clase': dia_clase,
                'feriados': feriados,
                'pruebas': pruebas,
                'fecha_examen_final': fecha_examen_final.strftime("%Y-%m-%d")
            }
            
            # Botones de descarga según privilegio
            if st.session_state.privilegio == "Completo" and (plantilla_planeamiento or plantilla_cronograma):
                # Generar contexto para plantillas
                context = {}
                context_cronograma = {}
                
                for sesion in plan_semanal:
                    num = sesion["Sesion"]
                    pref = f"SESION_{num}_"
                    
                    # Contexto común
                    context[pref + "FECHA"] = sesion["Fecha"].strftime("%Y-%m-%d")
                    context[pref + "EVENTO"] = sesion["Evento"]
                    context_cronograma[pref + "FECHA"] = sesion["Fecha"].strftime("%Y-%m-%d")
                    context_cronograma[pref + "EVENTO"] = sesion["Evento"]
                    
                    if sesion["Evento"] == "Clase normal" and "Planificacion" in sesion:
                        p = sesion["Planificacion"]
                        
                        # Contexto completo para planeamiento SIN ICONOS (documento institucional)
                        context[pref + "UNIDAD"] = p["Unidad"]
                        context[pref + "CONTENIDO"] = p["Contenido"]
                        context[pref + "OBJETIVO"] = f"El estudiante será capaz de {p['Verbo']} {p['Concepto']}"
                        context[pref + "NIVEL_BLOOM"] = p["Nivel"]
                        context[pref + "RETROALIMENTACION"] = f"Retroalimentación: {random.choice(retro)}"
                        context[pref + "INTRODUCCION"] = f"Introducción: {random.choice(intro)}"
                        context[pref + "INICIO"] = f"Inicio: {random.choice(inicio)}"
                        context[pref + "DESARROLLO"] = f"Desarrollo: {p['Actividad']}"
                        context[pref + "CIERRE"] = f"Cierre: {random.choice(cierre)}"
                        context[pref + "RECURSOS"] = f"Recursos: {', '.join(recursos_bloom[p['Nivel']])}"
                        context[pref + "EVALUACION"] = f"Evaluación: {', '.join(evaluacion_bloom[p['Nivel']])}"
                        
                        # Contexto resumido para cronograma
                        context_cronograma[pref + "UNIDAD"] = p["Unidad"]
                        context_cronograma[pref + "CONTENIDO"] = p["Contenido"]
                        context_cronograma[pref + "OBJETIVO"] = f"El estudiante será capaz de {p['Verbo']} {p['Concepto']}"
                        context_cronograma[pref + "NIVEL_BLOOM"] = p["Nivel"]
                        
                    else:
                        # Campos vacíos para sesiones especiales
                        campos_vacios = ["UNIDAD", "CONTENIDO", "OBJETIVO", "NIVEL_BLOOM", 
                                       "RETROALIMENTACION", "INTRODUCCION", "INICIO", 
                                       "DESARROLLO", "CIERRE", "RECURSOS", "EVALUACION"]
                        for campo in campos_vacios:
                            context[pref + campo] = ""
                        
                        # Para cronograma solo los campos básicos
                        context_cronograma[pref + "UNIDAD"] = ""
                        context_cronograma[pref + "CONTENIDO"] = ""
                        context_cronograma[pref + "OBJETIVO"] = ""
                        context_cronograma[pref + "NIVEL_BLOOM"] = ""
                    
                    # Advertencia común SIN ICONOS
                    context[pref + "ADVERTENCIA"] = (
                        "ADVERTENCIA: Este día coincide con feriado." if sesion["En_feriado"] else ""
                    )
                    context_cronograma[pref + "ADVERTENCIA"] = (
                        "ADVERTENCIA: Este día coincide con feriado." if sesion["En_feriado"] else ""
                    )
                
                # Crear archivo ZIP para usuarios completos
                zip_buffer = crear_archivo_zip(
                    context, context_cronograma, 
                    plantilla_planeamiento, plantilla_cronograma,
                    out, unidades_originales, configuracion
                )
                
                if zip_buffer:
                    st.download_button(
                        label="📥 Descargar Archivos Completos (ZIP con Word + TXT)",
                        data=zip_buffer,
                        file_name=f"Planificacion_Completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            
            # Botón para descargar solo TXT (disponible para todos)
            txt_data, txt_filename = crear_archivo_txt(out, unidades_originales, configuracion)
            
            label_txt = "📄 Descargar Planificación (TXT)"
            if st.session_state.privilegio == "Estándar":
                label_txt = "📄 Descargar Planificación (Solo TXT - Versión Estándar)"
            
            st.download_button(
                label=label_txt,
                data=txt_data,
                file_name=txt_filename,
                mime="text/plain",
                use_container_width=True
            )
            
            # Mostrar resumen de la planificación
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Sesiones", 17)
            
            with col2:
                sesiones_normales = len([s for s in plan_semanal if s["Evento"] == "Clase normal"])
                st.metric("Sesiones de Clase", sesiones_normales)
            
            with col3:
                pruebas_count = len([s for s in plan_semanal if s["Evento"] == "Prueba parcial"])
                st.metric("Pruebas Parciales", pruebas_count)
            
            with col4:
                feriados_count = len([s for s in plan_semanal if s["En_feriado"]])
                st.metric("Días Feriados", feriados_count)
            
            # Mostrar distribución por niveles de Bloom
            st.subheader("📊 Distribución por Niveles de Bloom")
            
            if fragmentos_sesiones:
                niveles_count = {}
                for frag in fragmentos_sesiones:
                    nivel = frag["Nivel"]
                    niveles_count[nivel] = niveles_count.get(nivel, 0) + 1
                
                # Crear gráfico de barras simple con texto
                for nivel, count in niveles_count.items():
                    porcentaje = (count / len(fragmentos_sesiones)) * 100
                    st.write(f"**{nivel}**: {count} sesiones ({porcentaje:.1f}%)")
                    st.progress(porcentaje / 100)
            
            # Mostrar calendario visual
            st.subheader("📅 Calendario de Sesiones")
            
            # Crear tabla del calendario
            import pandas as pd
            
            calendar_data = []
            for sesion in plan_semanal:
                fecha_es = formatear_fecha_es(sesion["Fecha"])
                calendar_data.append({
                    "Sesión": sesion["Sesion"],
                    "Fecha": sesion["Fecha"].strftime("%d/%m/%Y"),
                    "Día": fecha_es.split(",")[0],  # Solo el día de la semana
                    "Evento": sesion["Evento"],
                    "Unidad": sesion.get("Planificacion", {}).get("Unidad", "-") if "Planificacion" in sesion else "-",
                    "Feriado": "⚠️" if sesion["En_feriado"] else ""
                })
            
            df_calendar = pd.DataFrame(calendar_data)
            
            # Aplicar estilos condicionales
            def highlight_rows(row):
                if row["Evento"] == "Examen final":
                    return ['background-color: #ffebee'] * len(row)
                elif row["Evento"] == "Prueba parcial":
                    return ['background-color: #fff3e0'] * len(row)
                elif row["Evento"] == "Retroalimentación":
                    return ['background-color: #e8f5e8'] * len(row)
                elif row["Evento"] == "Revisión de prueba":
                    return ['background-color: #e3f2fd'] * len(row)
                elif row["Feriado"] == "⚠️":
                    return ['background-color: #f3e5f5'] * len(row)
                else:
                    return [''] * len(row)
            
            st.dataframe(
                df_calendar.style.apply(highlight_rows, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            # Leyenda mejorada
            st.caption("🟨 Pruebas parciales | 🟥 Examen final | 🟩 Retroalimentación | 🟦 Revisión | 🟪 Feriados")
            
            # Mostrar detalles de pruebas y feriados
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📝 Calendario de Evaluaciones")
                for sesion in plan_semanal:
                    if sesion["Evento"] in ["Prueba parcial", "Examen final"]:
                        fecha_es = formatear_fecha_es(sesion["Fecha"])
                        if sesion["En_feriado"]:
                            st.warning(f"**Sesión {sesion['Sesion']}** - {sesion['Evento']}: {fecha_es} ⚠️ FERIADO")
                        else:
                            st.info(f"**Sesión {sesion['Sesion']}** - {sesion['Evento']}: {fecha_es}")
            
            with col2:
                if feriados:
                    st.subheader("🏖️ Feriados Programados")
                    for i, feriado in enumerate(feriados, 1):
                        # Manejar feriados que pueden ser tuplas o tipos incorrectos
                        fecha_valida = None
                        
                        if isinstance(feriado, tuple):
                            fecha_valida = feriado[0] if feriado and len(feriado) > 0 else None
                        elif hasattr(feriado, 'strftime'):
                            fecha_valida = feriado
                        
                        if fecha_valida and hasattr(fecha_valida, 'weekday'):
                            fecha_es = formatear_fecha_es(fecha_valida)
                            # Verificar si coincide con alguna sesión
                            sesion_coincide = next((s for s in plan_semanal if s["Fecha"] == fecha_valida), None)
                            if sesion_coincide:
                                st.warning(f"**Feriado {i}**: {fecha_es} - ⚠️ Coincide con Sesión {sesion_coincide['Sesion']}")
                            else:
                                st.success(f"**Feriado {i}**: {fecha_es} - ✅ No afecta clases")
                        else:
                            st.error(f"**Feriado {i}**: Fecha inválida")
                    
                    # Mostrar resumen de impacto
                    feriados_con_clases = 0
                    for feriado in feriados:
                        fecha_valida = None
                        if isinstance(feriado, tuple):
                            fecha_valida = feriado[0] if feriado and len(feriado) > 0 else None
                        elif hasattr(feriado, 'strftime'):
                            fecha_valida = feriado
                        
                        if fecha_valida:
                            sesion_coincide = next((s for s in plan_semanal if s["Fecha"] == fecha_valida), None)
                            if sesion_coincide:
                                feriados_con_clases += 1
                    
                    if feriados_con_clases > 0:
                        st.warning(f"⚠️ **{feriados_con_clases}** feriado(s) coinciden con clases programadas")
                    else:
                        st.success("✅ Ningún feriado afecta las clases programadas")
                        
                else:
                    st.subheader("🏖️ Feriados")
                    st.info("No se han programado feriados")

if __name__ == "__main__":
    main()

