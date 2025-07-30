import streamlit as st
from datetime import datetime, timedelta, date
import io
import base64

# Importar de módulos personalizados
from constants import (
    verbos_bloom, plantillas_actividades, recursos_bloom,
    evaluacion_bloom, inicio, desarrollo, cierre, intro, retro,
    dias_semana
)
from utils import extraer_conceptos_simple, distribuir_unidades_10, genera_dict_unidades
from data_loaders import load_general_parameters, load_special_dates, load_academic_units
from planning_logic import generate_planning_data
from output_generators import generate_text_output, generate_word_documents, setup_streamlit_ui
from auth import login_screen, logout_button # Importar el nuevo módulo de autenticación

# Inicializar la interfaz de usuario de Streamlit y el estado de la sesión (estilos y títulos generales)
setup_streamlit_ui()

# Mostrar botón de cerrar sesión en la barra lateral si el usuario está logueado
logout_button()

# --- Pantalla de Inicio de Sesión ---
# Si el usuario no está logueado, mostrar la pantalla de login y detener la ejecución del resto de la app
if not st.session_state.get('logged_in'):
    login_screen()
else:
    # --- Interfaz de la Aplicación Principal (solo si el usuario ha iniciado sesión) ---
    st.title("📚 Planeamiento Semestral Bloom by emSoft")
    st.info("Complete los datos. Todas las fechas se eligen con el calendario. El examen final SIEMPRE es la sesión 17.")

    # --- 1. Parámetros Generales ---
    st.header("1. Parámetros Generales")
    fecha_inicio, fecha_fin, dia_clase = load_general_parameters()

    # --- 2. Feriados y Fechas Especiales ---
    st.header("2. Feriados y Fechas Especiales")
    feriado_date, feriado_btn_pressed, feriado_to_remove, remove_feriado_btn_pressed, \
        prueba1_date, prueba2_date, examen_final_date = load_special_dates()

    # Manejar la adición/eliminación de feriados
    if feriado_btn_pressed:
        if feriado_date not in st.session_state.feriados_list:
            st.session_state.feriados_list.append(feriado_date)
            st.session_state.feriados_list.sort()
            st.success(f"Feriado '{feriado_date.strftime('%d/%m/%Y')}' agregado.")
        else:
            st.warning("Ese feriado ya fue agregado.")

    if st.session_state.feriados_list:
        st.subheader("Feriados agregados:")
        st.write(f"Lista de Feriados: {', '.join([f.strftime('%d/%m/%Y') for f in st.session_state.feriados_list])}")
        if remove_feriado_btn_pressed:
            if feriado_to_remove:
                date_obj_to_remove = datetime.strptime(feriado_to_remove, '%d/%m/%Y').date()
                if date_obj_to_remove in st.session_state.feriados_list:
                    st.session_state.feriados_list.remove(date_obj_to_remove)
                    st.success(f"Feriado '{feriado_to_remove}' quitado.")
                else:
                    st.error("Error al quitar el feriado.")
            else:
                st.warning("Por favor, seleccione un feriado para quitar.")
    else:
        st.info("No hay feriados agregados aún.")


    # --- AYUDA PEDAGÓGICA ---
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

    # --- 3. Unidades Académicas ---
    st.header("3. Unidades Académicas")
    unidades_input = load_academic_units()

    # --- 4. Plantillas Word (.docx) ---
    # Solo cargar plantillas desde GitHub si el usuario es premium
    if st.session_state.user_type == 'premium':
        st.header("4. Plantillas Word (.docx)")
        # generate_word_documents ahora solo carga los bytes en session_state y no devuelve nada
        generate_word_documents()
    else:
        st.info("Las opciones de descarga de documentos Word (Plantillas) están disponibles para usuarios Premium.")


    st.markdown("<br>", unsafe_allow_html=True) # Espaciador

    if st.button("🚀 Generar Planificación", key="generate_plan_btn"):
        if not unidades_input:
            st.error("Debe ingresar al menos una unidad con título y contenido.")
        else:
            with st.spinner("Generando planificación..."):
                try:
                    unidades = genera_dict_unidades(unidades_input)
                    fechas_prueba = [prueba1_date, prueba2_date]
                    examen_final = examen_final_date

                    st.session_state.generated_context, st.session_state.generated_out_text = \
                        generate_planning_data(
                            fecha_inicio, fecha_fin, dia_clase, fechas_prueba, examen_final,
                            unidades, st.session_state.feriados_list, dias_semana,
                            verbos_bloom, plantillas_actividades, recursos_bloom, evaluacion_bloom,
                            inicio, desarrollo, cierre, intro, retro, extraer_conceptos_simple, distribuir_unidades_10
                        )
                    st.success("¡Planificación generada exitosamente! Consulte los resultados a continuación.")

                except Exception as e:
                    st.error(f"Error al generar la planificación: {str(e)}")

    # --- 5. Resultados ---
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
            # Solo mostrar botón de descarga de Planeamiento Word para usuarios premium
            if st.session_state.user_type == 'premium':
                if st.session_state.plantilla_planeamiento_bytes and st.session_state.generated_context:
                    try:
                        from docxtpl import DocxTemplate # Importar aquí para uso específico
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
                    except ImportError:
                        st.error("La librería 'python-docx-template' no está instalada.")
                    except Exception as e:
                        st.error(f"Error al preparar el documento de planeamiento: {str(e)}")
                else:
                    st.warning("Las plantillas de Word no se han cargado correctamente. Asegúrese de que las URLs de GitHub sean accesibles o que sea un usuario Premium.")
            else:
                st.info("Descarga de Planeamiento Word solo para usuarios Premium.")


        with col_download_cron:
            # Solo mostrar botón de descarga de Cronograma Word para usuarios premium
            if st.session_state.user_type == 'premium':
                if st.session_state.plantilla_cronograma_bytes and st.session_state.generated_context:
                    try:
                        from docxtpl import DocxTemplate # Importar aquí para uso específico
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
                    except ImportError:
                        st.error("La librería 'python-docx-template' no está instalada.")
                    except Exception as e:
                        st.error(f"Error al preparar el documento de cronograma: {str(e)}")
                else:
                    st.warning("Las plantillas de Word no se han cargado correctamente. Asegúrese de que las URLs de GitHub sean accesibles o que sea un usuario Premium.")
            else:
                st.info("Descarga de Cronograma Word solo para usuarios Premium.")


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
