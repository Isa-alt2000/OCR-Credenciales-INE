import easyocr


def aplicar_ocr_easyocr(regiones_extraidas):
    """
    Aplica EasyOCR a cada región extraída

    Args:
        regiones_extraidas: diccionario con las imágenes de cada región

    Returns:
        diccionario con los textos extraídos de cada campo
    """
    reader = easyocr.Reader(['es', 'en'], gpu=False)

    resultados = {}

    for campo, imagen in regiones_extraidas.items():
        print(f"Procesando campo: {campo}")

        # EasyOCR puede recibir directamente el numpy array
        # detail=0 devuelve solo el texto, detail=1 devuelve coordenadas también
        resultado = reader.readtext(imagen, detail=0)

        # Unir todos los textos detectados en un solo string
        texto = ' '.join(resultado).strip()

        resultados[campo] = texto
        print(f"  → {campo}: {texto}")

    return resultados
