import re
import json
from datetime import datetime


def guardar_json_con_fecha(datos):
    """
    Guarda JSON con timestamp y variable personalizada
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"resultado_{timestamp}.json"

    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

    print(f"JSON guardado en: {nombre_archivo}")
    return nombre_archivo
