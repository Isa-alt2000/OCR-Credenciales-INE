import json
import datetime
from extraccion import INEExtractor

RUTA_IMG = "ine_4.jpg"
DEBUG = True
FORZAR_PREPROCESAMIENTO = True

nombre_base = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def main():
    ine = INEExtractor(nombre_base=nombre_base)

    resultado_final, img_final = ine.procesar_ine(RUTA_IMG, nombre_base, debug=DEBUG, forzar=FORZAR_PREPROCESAMIENTO)

    if DEBUG:
        print(f'\nResultado final:\n{json.dumps(resultado_final, ensure_ascii=False, indent=4)}')
        ine.visualizar_detecciones(img_final)


if __name__ == '__main__':
    main()
