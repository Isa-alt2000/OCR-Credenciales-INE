import re


def fuzzy_similar(a, b):
    a, b = a.replace(" ", ""), b.replace(" ", "")
    iguales = sum(x == y for x, y in zip(a, b))
    return iguales / max(len(a), len(b))


def parsear_datos_ine(texto_completo):
    lineas = [l.strip() for l in texto_completo.splitlines() if l.strip()]
    datos = {
        "apellido_paterno": "",
        "apellido_materno": "",
        "nombre": "",
        "fecha_nacimiento": "",
        "sexo": "",
        "domicilio": "",
        "curp": "",
        "clave_elector": "",
    }

    esperando_domicilio = False

    EXCLUIR = {
        "SEX", "SEXO", "SEXQ", "MUESTRA", "NOMBRE", "FECHA", "CLAVE",
        "CURP", "DOMICILIO", "REGISTRO", "AÑO", "LOCALIDAD",
        "ESTADO", "VIGENCIA", "EMISIÓN"
    }

    def es_linea_valida(linea):
        l = linea.strip().upper()
        if not re.match(r"^[A-ZÁÉÍÓÚÑ\s]+$", l):
            return False
        if any(pal in l for pal in EXCLUIR):
            return False
        if len(l.split()) > 5 or len(l) < 2:
            return False
        return True

    for i, linea in enumerate(lineas):
        linea_may = linea.upper()

        # Fecha de nacimiento
        if re.search(r"\d{2}/\d{2}/\d{4}", linea):
            datos["fecha_nacimiento"] = re.search(r"\d{2}/\d{2}/\d{4}", linea).group()
            continue

        # Sexo
        if re.fullmatch(r"[MHF]", linea_may):
            datos["sexo"] = linea_may

            # deteccion secudnaria
            if i + 1 < len(lineas):
                posible_nombre = lineas[i + 1].strip()
                if es_linea_valida(posible_nombre):
                    datos["nombre"] = posible_nombre
            continue

        # Bloque NOMBRE
        if fuzzy_similar(linea_may, "NOMBRE") > 0.6:
            posibles_nombres = []
            for j in range(i + 1, min(i + 8, len(lineas))):
                l = lineas[j].strip()
                if es_linea_valida(l):
                    posibles_nombres.append(l)
                elif any(stop in l for stop in ["DOMICILIO", "CLAVE", "SEXO"]):
                    break

            if len(posibles_nombres) >= 3:
                datos["apellido_paterno"] = posibles_nombres[0]
                datos["apellido_materno"] = posibles_nombres[1]
                datos["nombre"] = " ".join(posibles_nombres[2:])
            elif len(posibles_nombres) == 2:
                datos["apellido_paterno"] = posibles_nombres[0]
                datos["apellido_materno"] = posibles_nombres[1]
            elif len(posibles_nombres) == 1:
                datos["apellido_paterno"] = posibles_nombres[0]
            continue

        # Domicilio
        if fuzzy_similar(linea_may, "DOMICILIO") > 0.6:
            esperando_domicilio = True
            continue
        if esperando_domicilio:
            if "CLAVE DE ELECTOR" in linea_may:
                esperando_domicilio = False
            else:
                datos["domicilio"] += linea + " "
                continue

        # CURP
        if fuzzy_similar(linea_may, "CURP") > 0.75:
            partes = linea.split("CURP", 1)
            if len(partes) > 1 and partes[1].strip():
                datos["curp"] = partes[1].strip().replace(":", "").replace(" ", "")
            elif i + 1 < len(lineas):
                posible_curp = lineas[i + 1].strip().replace(" ", "").replace(":", "")
                datos["curp"] = posible_curp
            continue

        # Reemplaza tu sección de "Clave elector" con esto:

        # Clave de elector
        if re.search(r'CLAVE\s*DE\s*ELECTOR', linea_may):
            # Extraer todo lo que viene después de "CLAVE DE ELECTOR"
            match = re.search(r'CLAVE\s*DE\s*ELECTOR\s*([A-Z0-9]{18})', linea_may.replace(" ", ""))
            if match:
                datos["clave_elector"] = match.group(1)
                continue

            # Si no encuentra en la misma línea, buscar en la siguiente
            partes = re.split(r'CLAVE\s*DE\s*ELECTOR', linea_may, 1)
            if len(partes) > 1:
                candidato = re.sub(r'[^A-Z0-9]', '', partes[1])
                if 16 <= len(candidato) <= 20:
                    datos["clave_elector"] = candidato
                    continue
            elif i + 1 < len(lineas):
                candidato = re.sub(r'[^A-Z0-9]', '', lineas[i + 1])
                if 16 <= len(candidato) <= 20:
                    datos["clave_elector"] = candidato
            continue

    for k in datos:
        datos[k] = datos[k].strip()

    return datos


def combinar_jsons(json1, json2):
    combinado = {}

    for clave in json1:
        val1 = json1.get(clave, "").strip()
        val2 = json2.get(clave, "").strip()

        if not val1 and val2:
            combinado[clave] = val2
            continue
        if not val2 and val1:
            combinado[clave] = val1
            continue

        # Si ambos tienen texto elegir el más largo
        if len(val2) > len(val1):
            combinado[clave] = val2
        else:
            combinado[clave] = val1

    return combinado
