import cv2
from preprocesamiento import REGIONES_INE, main_alineadores, procesado


def test_regiones_rapido_img(img, regiones):
    for nombre, (y1, y2, x1, x2) in regiones.items():
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, nombre, (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imwrite('test_regiones.jpg', img)
    return img


alinear = main_alineadores('ine_2.jpg', 'ine_referencia.jpg')
procesada = procesado(alinear)
img = test_regiones_rapido_img(procesada, REGIONES_INE)