# utils.py
import re
from collections import Counter

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
    sesiones_totales = 10 # Hardcoded as in original logic

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