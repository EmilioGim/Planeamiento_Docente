# planning_logic.py
import streamlit as st
from datetime import timedelta
import random

def generate_planning_data(
    fecha_inicio, fecha_fin, dia_clase, fechas_prueba, examen_final,
    unidades, feriados_list, dias_semana,
    verbos_bloom, plantillas_actividades, recursos_bloom, evaluacion_bloom,
    inicio, desarrollo, cierre, intro, retro, extraer_conceptos_simple, distribuir_unidades_10
):
    total_sesiones = 17
    dia_clase_num = dias_semana[dia_clase]
    fechas_sesiones = []
    f = fecha_inicio
    while len(fechas_sesiones) < total_sesiones:
        if f.weekday() == dia_clase_num and f not in feriados_list:
            fechas_sesiones.append(f)
            f += timedelta(days=7)
        else:
            f += timedelta(days=1)

    for i, pr in enumerate(fechas_prueba):
        if pr not in fechas_sesiones:
            st.warning(f"La fecha de Prueba {i+1} ({pr.strftime('%d/%m/%Y')}) no es un día de clase válido o coincide con un feriado.")
    if examen_final not in fechas_sesiones:
        st.warning(f"La fecha del Examen Final ({examen_final.strftime('%d/%m/%Y')}) no es un día de clase válido o coincide con un feriado.")

    sesiones_tipos = ["Clase normal"] * total_sesiones
    idx_prueba = []
    for pr in fechas_prueba:
        if pr in fechas_sesiones:
            idx_prueba.append(fechas_sesiones.index(pr))

    # Asegurar que el examen final siempre sea la última sesión calculada
    if fechas_sesiones and fechas_sesiones[-1] == examen_final:
        sesiones_tipos[-1] = "Examen final"
    else:
        # Si la fecha del examen final ingresada no coincide con la última sesión calculada,
        # se fuerza la última sesión calculada a ser el examen final.
        if fechas_sesiones:
            st.warning(f"La fecha de examen final ({examen_final.strftime('%d/%m/%Y')}) no corresponde a la última sesión calculada ({fechas_sesiones[-1].strftime('%d/%m/%Y')}). La última sesión se marcará como Examen Final.")
            sesiones_tipos[-1] = "Examen final"
        else:
            st.warning("No se pudieron calcular suficientes sesiones de clase para asignar el Examen Final.")

    for i, idx in enumerate(idx_prueba):
        if 0 <= idx < total_sesiones:
            # Sesión previa a la prueba (retroalimentación)
            if idx > 0 and sesiones_tipos[idx-1] == "Clase normal":
                sesiones_tipos[idx-1] = "Retroalimentación"
            # Sesión de la prueba
            sesiones_tipos[idx] = "Prueba parcial"
            # Sesión posterior a la prueba (revisión)
            if idx < len(sesiones_tipos) - 1 and sesiones_tipos[idx+1] == "Clase normal":
                sesiones_tipos[idx+1] = "Revisión de prueba"

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
        concepto = ", ".join(conceptos) if conceptos else fragmento[:50] + "..." # Fallback if no concepts
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

    for idx, (tipo, fecha) in enumerate(zip(sesiones_tipos, fechas_sesiones)):
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
                    "Desarrollo": random.choice(desarrollo),
                    "Cierre": random.choice(cierre)
                }
            else:
                # Fallback for extra "Clase normal" sessions without assigned content
                sesion_dict["Planificacion"] = {
                    "Unidad": "Sin unidad asignada", "Contenido": "Sin contenido asignado",
                    "Verbo": "N/A", "Concepto": "N/A", "Nivel": "N/A", "Actividad": "N/A",
                    "Recursos": "N/A", "Evaluacion": "N/A", "Retroalimentacion": "N/A",
                    "Introduccion": "N/A", "Inicio": "N/A", "Desarrollo": "N/A", "Cierre": "N/A"
                }
            idx_normal += 1
        else:
            # For non-"Clase normal" events, planning details are empty
            sesion_dict["Planificacion"] = {
                "Unidad": "", "Contenido": "", "Verbo": "", "Concepto": "",
                "Nivel": "", "Actividad": "", "Recursos": "", "Evaluacion": "",
                "Retroalimentacion": "", "Introduccion": "", "Inicio": "", "Desarrollo": "", "Cierre": ""
            }

        lista_sesiones_word.append(sesion_dict)

    context = {
        "PERIODO": f"{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}",
        "DIA_CLASE": dia_clase.capitalize(),
        "FERIADOS": ', '.join([f.strftime('%d/%m/%Y') for f in feriados_list]) if feriados_list else "Ninguno",
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

    out_text = generate_text_output(fecha_inicio, fecha_fin, dia_clase, fechas_prueba,
                                   fechas_sesiones, unidades, lista_sesiones_word, feriados_list)

    return context, out_text