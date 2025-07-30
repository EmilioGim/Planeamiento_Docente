# planning_logic.py
# planning_logic.py
import streamlit as st
from datetime import datetime, timedelta, date
import random
import re
from collections import Counter

# Asegúrate de importar generate_text_output desde output_generators
from output_generators import generate_text_output
from constants import (
    verbos_bloom, plantillas_actividades, recursos_bloom, evaluacion_bloom,
    inicio, desarrollo, cierre, intro, retro, dias_semana
)
from utils import extraer_conceptos_simple, distribuir_unidades_10, genera_dict_unidades

def generar_titulo_sesion(sesion_info, unidades_dict):
    """Genera un título descriptivo para la sesión."""
    evento = sesion_info.get("Evento", "Clase normal")
    if evento == "Clase normal":
        planificacion = sesion_info.get("Planificacion", {})
        unidad_num = planificacion.get("Unidad_Numero")
        if unidad_num is not None:
            unidad_titulo = unidades_dict.get(unidad_num, {}).get("titulo", "Unidad Desconocida")
            concepto = planificacion.get("Concepto", "")
            return f"Clase: {unidad_titulo} - {concepto}"
        else:
            return "Clase normal (sin planificación)"
    elif evento == "Recuperación de Prueba":
        return f"Recuperación de Prueba {sesion_info.get('Numero_Prueba', '')}"
    elif evento == "Examen Final":
        return "Examen Final"
    elif evento == "Prueba":
        return f"Prueba {sesion_info.get('Numero_Prueba', '')}"
    else:
        return evento # Para feriados u otros eventos

def generate_planning_data(
    fecha_inicio, fecha_fin, dia_clase, fechas_prueba, examen_final,
    unidades, feriados_list, dias_semana,
    verbos_bloom, plantillas_actividades, recursos_bloom, evaluacion_bloom,
    inicio, desarrollo, cierre, intro, retro, extraer_conceptos_simple, distribuir_unidades_10
):
    """
    Genera el contexto completo para la planificación semestral,
    incluyendo fechas de sesiones, planificación por sesión y el texto de salida.
    """
    # Calcular fechas de sesiones
    fechas_sesiones = []
    current_date = fecha_inicio
    dia_clase_num = dias_semana[dia_clase.lower()]

    while current_date <= fecha_fin:
        if current_date.weekday() == dia_clase_num and current_date not in feriados_list:
            fechas_sesiones.append(current_date)
        current_date += timedelta(days=1)

    if not fechas_sesiones:
        raise ValueError("No se encontraron fechas de clase en el período seleccionado. Verifique las fechas y el día de clase.")

    # Asegurarse de que el examen final sea la última sesión
    # Esto ya debería estar manejado en data_loaders/app.py para la fecha del examen final.
    # Aquí solo nos aseguramos de que el último elemento de fechas_sesiones sea el examen final
    # si examen_final ya está en fechas_sesiones.
    if examen_final not in fechas_sesiones:
        # Si el examen final no está en las sesiones calculadas (por ser feriado o día incorrecto),
        # lo insertamos al final o lo reemplazamos si el último día de clase es el mismo.
        if examen_final.weekday() == dia_clase_num:
             fechas_sesiones.append(examen_final)
             fechas_sesiones = sorted(list(set(fechas_sesiones))) # Eliminar duplicados y reordenar
        else:
            # Si el día de la semana del examen final no coincide con el día de clase,
            # podríamos ajustarlo o emitir una advertencia. Por ahora, lo añadimos si no existe
            # o lo dejamos como está si ya se agregó manualmente en app.py.
            pass # Ya se manejaría la lógica de add_examen_final_to_fechas_sesiones en app.py

    # Distribuir unidades en sesiones
    distribucion_sesiones = distribuir_unidades_10(unidades, len(fechas_sesiones) - 1) # -1 por el examen final

    lista_sesiones_word = []
    sesion_counter = 0

    unidades_dict = {u['numero']: u for u in unidades} # Para fácil acceso por número de unidad

    for i, fecha_sesion in enumerate(fechas_sesiones):
        evento = "Clase normal"
        planificacion = {}
        en_feriado = False
        numero_prueba = None

        if fecha_sesion in feriados_list:
            evento = "Feriado"
            en_feriado = True
        elif fecha_sesion == examen_final:
            evento = "Examen Final"
        elif fecha_sesion in fechas_prueba:
            evento = "Prueba"
            numero_prueba = fechas_prueba.index(fecha_sesion) + 1 # Asignar número de prueba
        elif i < len(distribucion_sesiones): # Para sesiones de clase normal
            sesion_counter += 1
            unidad_actual = distribucion_sesiones[i]
            if unidad_actual:
                unidad_info = unidades_dict.get(unidad_actual['numero_unidad'])
                if unidad_info:
                    contenido_linea = unidad_info['lineas'][unidad_actual['indice_contenido_linea']]
                    concepto_extraido = extraer_conceptos_simple(contenido_linea)

                    # Seleccionar un verbo de Bloom aleatorio del nivel Aplicar o superior
                    niveles_aplicables = ["Aplicar", "Analizar", "Evaluar", "Crear"]
                    nivel_bloom_elegido = random.choice(niveles_aplicables)
                    verbo_elegido = random.choice(verbos_bloom.get(nivel_bloom_elegido, ["realizar"]))

                    # Seleccionar plantillas aleatorias
                    actividad_elegida = random.choice(plantillas_actividades.get(nivel_bloom_elegido, ["Actividad general"]))
                    recurso_elegido = random.choice(recursos_bloom.get(nivel_bloom_elegido, ["Recurso general"]))
                    evaluacion_elegida = random.choice(evaluacion_bloom.get(nivel_bloom_elegido, ["Evaluación general"]))
                    inicio_elegido = random.choice(inicio)
                    desarrollo_elegido = random.choice(desarrollo)
                    cierre_elegido = random.choice(cierre)
                    intro_elegida = random.choice(intro)
                    retro_elegida = random.choice(retro)

                    planificacion = {
                        "Unidad_Numero": unidad_info['numero'],
                        "Unidad": unidad_info['titulo'],
                        "Contenido": contenido_linea,
                        "Verbo": verbo_elegido,
                        "Concepto": concepto_extraido,
                        "Nivel": nivel_bloom_elegido,
                        "Actividad": actividad_elegida.format(concepto_extraido),
                        "Retroalimentacion": retro_elegida,
                        "Introduccion": intro_elegida,
                        "Inicio": inicio_elegido,
                        "Desarrollo": desarrollo_elegido,
                        "Cierre": cierre_elegido,
                        "Recursos": recurso_elegido,
                        "Evaluacion": evaluacion_elegida,
                    }
                else:
                    evento = "Clase normal (unidad no encontrada)"
        elif i == (len(fechas_sesiones) - 1) and evento != "Examen Final": # Ultima sesion si no es el examen
             evento = "Sesión final de repaso" # O un evento por defecto si no es el examen

        lista_sesiones_word.append({
            "Numero": i + 1, # Número de sesión basado en el índice
            "Fecha": fecha_sesion.strftime('%d/%m/%Y'),
            "Evento": evento,
            "Planificacion": planificacion,
            "En_feriado": en_feriado,
            "Numero_Prueba": numero_prueba
        })

    # Preparar el contexto para los documentos Word
    context = {
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "dia_clase": dia_clase.capitalize(),
        "feriados": ", ".join([f.strftime('%d/%m/%Y') for f in feriados_list]) if feriados_list else "Ninguno",
        "fechas_pruebas": ", ".join([f.strftime('%d/%m/%Y') for f in fechas_prueba if f in fechas_sesiones]) if [f for f in fechas_prueba if f in fechas_sesiones] else "No programadas",
        "examen_final_fecha": examen_final.strftime('%d/%m/%Y'),
        "unidades_programadas": [{"Numero": u['numero'], "Titulo": u['titulo']} for u in unidades],
        "sesiones": lista_sesiones_word
    }

    # Generar el texto de salida para la visualización en pantalla
    # Aquí se llama a generate_text_output con los datos procesados.
    out_text = generate_text_output(fecha_inicio, fecha_fin, dia_clase,
                                    fechas_prueba, fechas_sesiones, unidades,
                                    lista_sesiones_word, feriados_list)

    return context, out_text
