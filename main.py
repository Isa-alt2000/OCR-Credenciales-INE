from preprocesamiento import alinear_ine_principal, extraer_regiones, REGIONES_INE
from extraccion import aplicar_ocr_easyocr
from parseo_json import guardar_json_con_fecha

RUTA_IMG = "ine_2.jpg"
DEBUG = True

referencia = "ine_referencia.jpg"


def main():
    alineado = alinear_ine_principal(RUTA_IMG, referencia)
    prepro = extraer_regiones(alineado, REGIONES_INE)   
    resultados = aplicar_ocr_easyocr(prepro)
    guardar_json_con_fecha(resultados)


if __name__ == '__main__':
    main()